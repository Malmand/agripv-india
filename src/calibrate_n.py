"""State nitrogen calibration for wheat and pearl millet + legume yield-gap factors.
Picks, per state and crop, the N level (10*,30,60,90,120,180 kg/ha) whose simulated open-field
state yield (2-GCM mean, MapSPAM area and irrigation-share weighted) is closest to the ICRISAT
1995-2014 state mean. *10 = farmer-practice millet run. Writes prod/calib_n.csv,
results/calib_state_yields.csv, results/yieldgap_legumes.csv, results/validation_before_after.csv.
"""
import glob
import numpy as np
import pandas as pd

g = pd.read_csv('data/grid_india_025.csv')
crops = ['wheat', 'chickpea', 'groundnut', 'pearl_millet']
irr = g.melt(id_vars=['cell_id', 'state'], value_vars=[f'{c}_irr_share' for c in crops], var_name='crop', value_name='irr')
irr['crop'] = irr.crop.str.replace('_irr_share', '')
area = g.melt(id_vars=['cell_id'], value_vars=[f'{c}_ha' for c in crops], var_name='crop', value_name='ha')
area['crop'] = area.crop.str.replace('_ha', '')
GCMS = ['GFDL-ESM4', 'MPI-ESM1-2-HR']


def state_yield(t):
    t = t[t.model.isin(GCMS)]
    m = t.groupby(['cell', 'crop', 'water']).open_mean.mean().reset_index()
    m = m.merge(irr.rename(columns={'cell_id': 'cell'}), on=['cell', 'crop'])
    m['irr'] = m.irr.fillna(0)
    m['w'] = np.where(m.water == 'ir', m.irr, 1 - m.irr)
    m['w'] = m.w / m.groupby(['cell', 'crop']).w.transform('sum')
    c = m.assign(y=m.w * m.open_mean).groupby(['cell', 'crop', 'state']).y.sum().reset_index()
    c = c.merge(area.rename(columns={'cell_id': 'cell'}), on=['cell', 'crop'])
    return c.groupby(['state', 'crop']).apply(lambda d: np.average(d.y, weights=d.ha), include_groups=False).rename('sim').reset_index()


# observed
k = pd.read_csv('data/yields/kaggle_raw/ICRISAT-District Level Data.csv')
k = k[(k.Year >= 1995) & (k.Year <= 2014)]
name = {'wheat': 'WHEAT', 'chickpea': 'CHICKPEA', 'groundnut': 'GROUNDNUT', 'pearl_millet': 'PEARL MILLET'}
rows = []
for cr, n in name.items():
    s = k.groupby(['State Name', 'Year'])[[f'{n} AREA (1000 ha)', f'{n} PRODUCTION (1000 tons)']].sum().reset_index()
    s = s[s[f'{n} AREA (1000 ha)'] > 0]
    s['y'] = s[f'{n} PRODUCTION (1000 tons)'] / s[f'{n} AREA (1000 ha)'] * 1000
    o = s.groupby('State Name').agg(obs=('y', 'mean'), obs_area=(f'{n} AREA (1000 ha)', 'mean')).reset_index()
    o['crop'] = cr
    rows.append(o)
obs = pd.concat(rows).rename(columns={'State Name': 'state'})
obs['state'] = obs.state.replace({'Orissa': 'Odisha'})

farmer = pd.read_csv('runs/india_test/it/summary/ry_system_historical_farmer_open.csv.gz')
levels = {}
for f in sorted(glob.glob('runs/calib/cal/ry_system_historical_n*_open.csv.gz')):
    n = int(f.split('_n')[1].split('_')[0])
    levels[n] = state_yield(pd.read_csv(f))
levels[10] = state_yield(farmer[farmer.crop == 'pearl_millet'])
lv = pd.concat([d.assign(n=n) for n, d in levels.items()])
lv = lv[~((lv.crop == 'wheat') & (lv.n == 10))]
lv = lv.merge(obs, on=['state', 'crop'])
lv['err'] = (lv.sim / lv.obs - 1).abs()
best = lv.loc[lv.groupby(['state', 'crop']).err.idxmin()].copy()
best = best[best.obs_area >= 20]   # states with >= 20 kha of the crop

# fallback per crop: area-weighted median of state choices
def wmedian(d):
    d = d.sort_values('n')
    c = d.obs_area.cumsum().values
    return int(d.n.values[np.searchsorted(c, c[-1] / 2)])


fb = best.groupby('crop').apply(wmedian, include_groups=False)
calib = pd.concat([best[['state', 'crop', 'n']], pd.DataFrame({'state': 'ALL', 'crop': fb.index, 'n': fb.values})])
calib.to_csv('prod/calib_n.csv', index=False)
lv.to_csv('results/calib_state_yields.csv', index=False)

# before (farmer, national N) vs after (calibrated)
before = state_yield(farmer).merge(obs, on=['state', 'crop'])
after = best[['state', 'crop', 'sim', 'obs', 'obs_area', 'n']]
nuse = pd.read_csv('data/yields/state_n_use_1995_2014.csv').rename(columns={'State Name': 'state'})
nuse['state'] = nuse.state.replace({'Orissa': 'Odisha'})
pd.set_option('display.width', 220)
for cr in ['wheat', 'pearl_millet']:
    b = before[(before.crop == cr) & (before.obs_area >= 50)]
    a = after[(after.crop == cr) & (after.obs_area >= 50)].merge(nuse, on='state', how='left')
    print(f'\n== {cr} ==')
    print(f'before: r={np.corrcoef(b.sim, b.obs)[0,1]:.2f}  wsim/obs={np.average(b.sim/b.obs, weights=b.obs_area):.2f}  '
          f'MAPE={np.average((b.sim/b.obs-1).abs(), weights=b.obs_area):.2f}')
    print(f'after : r={np.corrcoef(a.sim, a.obs)[0,1]:.2f}  wsim/obs={np.average(a.sim/a.obs, weights=a.obs_area):.2f}  '
          f'MAPE={np.average((a.sim/a.obs-1).abs(), weights=a.obs_area):.2f}')
    print('rank corr calibrated N vs state fertiliser N use:', round(a[['n', 'kgN_per_ha_gca']].corr(method='spearman').iloc[0, 1], 2))
    print(a.sort_values('obs_area', ascending=False)[['state', 'obs_area', 'obs', 'sim', 'n', 'kgN_per_ha_gca']].round(0).to_string(index=False))
print('\nfallback N:', fb.to_dict())

# legume yield-gap factors (absolute yields only)
leg = before[before.crop.isin(['chickpea', 'groundnut'])].copy()
leg['gap_factor'] = (leg.obs / leg.sim).round(3)
leg.to_csv('results/yieldgap_legumes.csv', index=False)
print('\nlegume yield-gap factors (obs/sim), states >=50 kha:')
print(leg[leg.obs_area >= 50].groupby('crop').apply(lambda d: pd.Series({'states': len(d),
      'area_wtd_factor': np.average(d.gap_factor, weights=d.obs_area)}), include_groups=False).round(2))
pd.concat([before.assign(case='before'), after.assign(case='after')]).to_csv('results/validation_before_after.csv', index=False)
