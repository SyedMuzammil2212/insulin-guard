import * as SecureStore from 'expo-secure-store';
const base = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
type Tokens = {access_token:string;refresh_token:string};
let tokens:Tokens|null = null;
let refreshing:Promise<boolean>|null = null;
export async function loadTokens(){ const value=await SecureStore.getItemAsync('tokens'); tokens=value?JSON.parse(value):null; return !!tokens; }
export async function setTokens(value:Tokens|null){ tokens=value; if(value) await SecureStore.setItemAsync('tokens',JSON.stringify(value)); else await SecureStore.deleteItemAsync('tokens'); }
async function rotate(){
  if(!tokens) return false;
  try { const response=await fetch(`${base}/auth/refresh`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({refresh_token:tokens.refresh_token})}); if(!response.ok){await setTokens(null); return false;} await setTokens(await response.json()); return true; } catch { return false; }
}
export async function api<T>(path:string, options:RequestInit={}, retry=true):Promise<T>{
  const response=await fetch(`${base}${path}`,{...options,headers:{'Content-Type':'application/json',...(tokens?{Authorization:`Bearer ${tokens.access_token}`}:{ }),...options.headers}});
  if(response.status===401 && tokens && retry && !path.startsWith('/auth/')){ refreshing ??= rotate().finally(()=>{refreshing=null}); if(await refreshing) return api<T>(path,options,false); }
  if(!response.ok){let message=`Request failed (${response.status})`; try {const data=await response.json(); if(typeof data.detail==='string') message=data.detail; else if(Array.isArray(data.detail)){const errors=data.detail.flatMap((item:unknown)=>{if(!item || typeof item!=='object') return []; const {loc,msg}=item as {loc?:unknown;msg?:unknown}; if(typeof msg!=='string') return []; const field=Array.isArray(loc)?loc.filter((part:unknown)=>typeof part==='string' && part!=='body').join(' '):''; return [field?`${field}: ${msg}`:msg];}); if(errors.length) message=errors.join('\n');}} catch {} throw new Error(message);}
  if(response.status===204) return undefined as T;
  return response.json();
}
export async function signOut(){const refresh=tokens?.refresh_token; try {if(refresh) await api('/auth/logout',{method:'POST',body:JSON.stringify({refresh_token:refresh})});} finally {await setTokens(null);}}
export function apiBase(){return base;}

export async function exportCsv(retry=true):Promise<string>{
  const response=await fetch(`${base}/export`,{headers:tokens?{Authorization:`Bearer ${tokens.access_token}`}:{}});
  if(response.status===401 && tokens && retry){refreshing ??= rotate().finally(()=>{refreshing=null});if(await refreshing)return exportCsv(false);}
  if(!response.ok)throw new Error(`Export failed (${response.status})`);
  return response.text();
}
