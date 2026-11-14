import hashlib,json
from src.services.prefixspan import mine_patterns
from src.services.edit_distance import representatives
from src.services.holdout import split_rows,group_sizes,side_stats
from src.constants.domain import MAX_UNIQUE_PATHS,HOLDOUT_PERCENT,HOLDOUT_SEED

def analyze(rows,dictionary,study):
 normalized=[]
 codes={e['code'] for e in dictionary['entries']}
 for r in rows:
  path=r['path']
  if not path or any(x not in codes for x in path):raise ValueError('空路径或未知触点')
  if study['collapse_repeats']:path=[x for i,x in enumerate(path) if i==0 or path[i-1]!=x]
  normalized.append({**r,'path':path})
 # Bound medoid work before either algorithm starts.
 if len({tuple(r['path']) for r in normalized})>MAX_UNIQUE_PATHS:raise ValueError('唯一序列超过160，请缩小样本或预先分组')
 holdout_enabled=bool(study.get('holdout_enabled'))
 if holdout_enabled:
  discovery,heldout=split_rows(normalized,HOLDOUT_SEED)
 else:
  discovery,heldout=normalized,[]
 patterns=mine_patterns(discovery,study['min_support'],study['max_length'])
 if holdout_enabled:
  heldout_sizes=group_sizes(heldout)
  for p in patterns['patterns']:
   # Hold-out rows never re-rank or filter; they only rescore the patterns found above.
   p.update({'heldout_'+k:v for k,v in side_stats(p['pattern'],heldout,heldout_sizes).items()})
  holdout_summary={'enabled':True,'seed':HOLDOUT_SEED,'percent':HOLDOUT_PERCENT,'discovery_journeys':len(discovery),'heldout_journeys':len(heldout),'discovery_group_sizes':group_sizes(discovery),'heldout_group_sizes':heldout_sizes,'patterns_recomputed':len(patterns['patterns'])}
 else:
  holdout_summary={'enabled':False,'seed':HOLDOUT_SEED,'percent':HOLDOUT_PERCENT,'discovery_journeys':len(discovery),'heldout_journeys':0,'discovery_group_sizes':group_sizes(discovery),'heldout_group_sizes':group_sizes([]),'patterns_recomputed':0}
 # Representative paths and exit alignment are descriptive of all journeys, never just the discovery split.
 medoids=representatives(normalized)
 limitations=['频繁子序列允许中间跳过触点，并非连续片段；支持度分母是旅程数，同一旅程每个模式最多计1次','转化/退出组支持差仅描述关联；模拟路径不用于因果或通道归因','编辑距离每次插入/删除/替换成本1，保留成本0；medoid按序列频数加权，平局按编码字典序','最近成功路径同距离时优先成功组频数高者，再按字典序；对齐平局优先保留、替换、删除、插入','最多2000旅程、每条20触点、160唯一序列、模式长度4、候选6000；结果最多展示200模式与12条退出对齐']
 if holdout_enabled:limitations.append(f'留出复验按转化/退出分别以旅程编号与固定种子{HOLDOUT_SEED}排序，各组向下取整留出{HOLDOUT_PERCENT}%；留出旅程只复算已发现模式的支持度，不参与筛选排序，两侧分母各自独立，空组留空')
 return {**patterns,**medoids,'dictionary':dictionary,'study':study,'journeys':len(rows),'group_sizes':group_sizes(normalized),'holdout':holdout_summary,'raw_events':sum(len(r['path']) for r in rows),'normalized_events':sum(len(r['path']) for r in normalized),'collapse_repeats':study['collapse_repeats'],'checksum':hashlib.sha256(json.dumps({'rows':rows,'dictionary':dictionary,'study':study},sort_keys=True).encode()).hexdigest(),'limitations':limitations}
