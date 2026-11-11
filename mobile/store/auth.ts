import {create} from 'zustand';
import {api,loadTokens,setTokens,signOut} from '../services/api';
import {User} from '../types';
type Auth = {user:User|null;ready:boolean;initialize:()=>Promise<void>;login:(email:string,password:string)=>Promise<void>;logout:()=>Promise<void>;reload:()=>Promise<void>};
export const useAuth=create<Auth>((set)=>({user:null,ready:false,initialize:async()=>{try{if(await loadTokens()) set({user:await api<User>('/auth/me')});}catch{} finally{set({ready:true});}},login:async(email,password)=>{const tokens=await api<{access_token:string;refresh_token:string}>('/auth/login',{method:'POST',body:JSON.stringify({email,password})});await setTokens(tokens);set({user:await api<User>('/auth/me')});},logout:async()=>{try{await signOut();}finally{set({user:null});}},reload:async()=>set({user:await api<User>('/auth/me')})}));
