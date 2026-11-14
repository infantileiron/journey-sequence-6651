import hashlib
from src.constants.domain import HOLDOUT_PERCENT,OUTCOMES

def _rank(seed,journey_id):
 # Ranking depends only on the fixed seed and journey id, not list position.
 return hashlib.sha256(f'{seed}|{journey_id}'.encode('utf-8')).hexdigest()
def split_rows(rows,seed):
 discovery=[];heldout=[]
 for outcome in OUTCOMES:
  group=[r for r in rows if r['outcome']==outcome]
  count=len(group)*HOLDOUT_PERCENT//100
  ranked=sorted(group,key=lambda r:(_rank(seed,r['journey_id']),r['journey_id']))
  heldout.extend(ranked[:count]);discovery.extend(ranked[count:])
 return discovery,heldout
def group_sizes(rows):return {g:sum(r['outcome']==g for r in rows) for g in OUTCOMES}
def contains(pattern,path):
 pos=0
 for symbol in path:
  if symbol==pattern[pos]:
   pos+=1
   if pos==len(pattern):return True
 return pos==len(pattern)
def side_stats(pattern,rows,sizes):
 matched=[r for r in rows if contains(pattern,r['path'])]
 converted=sum(r['outcome']=='converted' for r in matched);exited=len(matched)-converted
 converted_support=converted/sizes['converted'] if sizes['converted'] else None
 exited_support=exited/sizes['exited'] if sizes['exited'] else None
 return {'count':len(matched),'support':len(matched)/len(rows) if rows else None,'converted_count':converted,'exited_count':exited,'converted_support':converted_support,'exited_support':exited_support,'support_difference':converted_support-exited_support if converted_support is not None and exited_support is not None else None}
