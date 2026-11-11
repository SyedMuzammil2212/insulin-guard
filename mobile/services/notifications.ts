import * as Notifications from 'expo-notifications';
import * as SecureStore from 'expo-secure-store';
import {Reminder} from '../types';

// Expo daily triggers follow the device's local time zone. Do not silently shift a
// schedule entered for a different zone.
export async function scheduleReminder(reminder:Reminder){
  const deviceZone=Intl.DateTimeFormat().resolvedOptions().timeZone;
  if(reminder.timezone!==deviceZone) throw new Error(`This device uses ${deviceZone}; reminders can only be scheduled in its current time zone.`);
  const permission=await Notifications.requestPermissionsAsync();
  if(permission.status!=='granted') throw new Error('Notification permission was not granted.');
  const [hour,minute]=reminder.reminder_time.split(':').map(Number);
  const id=await Notifications.scheduleNotificationAsync({content:{title:reminder.title,body:'Open your journal to review your reminder.'},trigger:{type:Notifications.SchedulableTriggerInputTypes.DAILY,hour,minute}});
  await SecureStore.setItemAsync(`reminder-${reminder.id}`,id);
}
export async function cancelReminder(id:string){const key=`reminder-${id}`;const scheduled=await SecureStore.getItemAsync(key);if(scheduled)await Notifications.cancelScheduledNotificationAsync(scheduled);await SecureStore.deleteItemAsync(key);}
