import {Stack} from 'expo-router';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {useEffect} from 'react';
import {useAuth} from '../store/auth';
import {LoadingState} from '../components/ui';
const client=new QueryClient({defaultOptions:{queries:{retry:1}}});
export default function Root(){const ready=useAuth(s=>s.ready);const init=useAuth(s=>s.initialize);useEffect(()=>{init()},[init]);if(!ready)return <LoadingState/>;return <QueryClientProvider client={client}><Stack screenOptions={{headerShown:false}} /></QueryClientProvider>}
