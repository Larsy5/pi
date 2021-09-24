import requests
import time
import random
import os
import pickle
import dateutil.parser
from retrying import retry

api='https://socialchain.app'

def tostamp(timestr):
  dt = dateutil.parser.parse(timestr)
  stamp=int(time.mktime(dt.timetuple()))
  return stamp

on=os.getenv('on')
if on=='schedule':
  timing=True
else:
  timing=False
userpass=os.getenv('userpass')
userpass=userpass.split()
username=userpass[0]
password=userpass[1]
try:
  with open('tokens.txt','rb') as f:
    tokens=pickle.load(f)
    token=tokens[username]
except FileNotFoundError:
  tokens={}
  token=''
except KeyError:
  token=''
session=requests.Session()
session.headers.update({'authorization':'Bearer '+token})
if token=='' or session.get(api+'/api/pi').status_code!=200:
  login=session.post(api+'/api/password_sign_in',data={'phone_number':username,'password':password}).json()
  if 'error' in login:
    raise Exception(login['error'])
  else:
    token=login['credentials']['access_token']
  session.headers.update({'authorization':'Bearer '+token})
  with open('tokens.txt','wb') as f:
    tokens[username]=token
    pickle.dump(tokens,f)

me=session.get(api+'/api/pi').json()
is_mining=me['mining_status']['is_mining']
if is_mining==True:
  expires_at=me['mining_status']['expires_at']
  expires_at=tostamp(expires_at)
  now=time.time()
  diff=expires_at-now
  tmhour=time.localtime().tm_hour
  expires_hour=time.localtime(expires_at).tm_hour
  if tmhour!=expires_hour or diff>60:
    print('过期时间超过一小时')
    exit()
  else:
    time.sleep(diff)

if timing==True:
  thetime=random.randint(5,20)
  time.sleep(thetime*60)
  print('随机等待%smin'%thetime)

@retry(stop_max_attempt_number=10, wait_random_min=5*60000, wait_random_max=20*60000)
def reward():
  proof=session.post(api+'/api/proof_of_presences',data={'recaptcha_token':None})
  prstatus=proof.status_code
  if prstatus==200:
    print('续期成功')
  elif prstatus==500:
    prjson=proof.json()
    raise Exception(prjson['error'])
  elif prstatus==401:
    raise Exception('token已过期')
  else:
    try:
      prjson=proof.json()
      error=prjson['error']
      raise Exception('%s %s'%(prstatus,error))
    except json.decoder.JSONDecodeError:
      raise Exception(str(prstatus)+'未知错误')
reward()
