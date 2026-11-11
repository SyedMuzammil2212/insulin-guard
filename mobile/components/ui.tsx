import React from 'react';
import {ActivityIndicator,Pressable,ScrollView,StyleSheet,Text,TextInput,TextInputProps,useColorScheme,View} from 'react-native';
import {SafeAreaView} from 'react-native-safe-area-context';
export function useColors(){const dark=useColorScheme()==='dark';return dark?{bg:'#101d28',card:'#1a2c39',text:'#f3f8fa',muted:'#abc0ca',accent:'#58c6cb',border:'#39525e'}:{bg:'#f3f7f8',card:'#ffffff',text:'#12303d',muted:'#536e7b',accent:'#087c83',border:'#cadbdf'};}
export function Screen({children}:{children:React.ReactNode}){const c=useColors();return <SafeAreaView edges={['top']} style={{flex:1,backgroundColor:c.bg}}><ScrollView contentInsetAdjustmentBehavior="never" contentContainerStyle={s.screen} keyboardShouldPersistTaps="handled">{children}</ScrollView></SafeAreaView>}
export function Heading({children}:{children:React.ReactNode}){const c=useColors();return <Text style={[s.heading,{color:c.text}]}>{children}</Text>}
export function Body({children}:{children:React.ReactNode}){const c=useColors();return <Text style={{color:c.muted,lineHeight:21}}>{children}</Text>}
export function Card({children}:{children:React.ReactNode}){const c=useColors();return <View style={[s.card,{backgroundColor:c.card,borderColor:c.border}]}>{children}</View>}
export function Button({title,onPress,disabled=false}:{title:string;onPress:()=>void;disabled?:boolean}){const c=useColors();return <Pressable accessibilityRole="button" disabled={disabled} onPress={onPress} style={[s.button,{backgroundColor:c.accent,opacity:disabled?.5:1}]}><Text style={{color:'#fff',fontWeight:'700',textAlign:'center'}}>{title}</Text></Pressable>}
export function FormInput({label,...props}:TextInputProps & {label:string}){const c=useColors();return <View style={{gap:6}}><Text style={{color:c.text,fontWeight:'600'}}>{label}</Text><TextInput placeholderTextColor={c.muted} {...props} style={[s.input,{color:c.text,borderColor:c.border,backgroundColor:c.card},props.style]}/></View>}
export function LoadingState(){return <View style={{padding:30}}><ActivityIndicator accessibilityLabel="Loading" /></View>}
export function ErrorState({message}:{message:string}){return <Text accessibilityRole="alert" style={{color:'#c53737'}}>{message}</Text>}
export function MetricCard({label,value}:{label:string;value:string}){return <Card><Body>{label}</Body><Heading>{value}</Heading></Card>}
const s=StyleSheet.create({screen:{padding:20,gap:16,paddingBottom:48},heading:{fontSize:24,fontWeight:'700'},card:{borderRadius:18,padding:16,borderWidth:1,gap:8},button:{borderRadius:12,padding:15},input:{borderWidth:1,borderRadius:12,padding:12},});
