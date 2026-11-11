export type Unit = 'mg/dL' | 'mmol/L';
export type User = {id:string;name:string;email:string;preferred_glucose_unit:Unit;timezone:string;target_min:string|null;target_max:string|null};
export type Glucose = {id:string;glucose_value:string;unit:Unit;measurement_context:string;measured_at:string;notes?:string};
export type Insulin = {id:string;insulin_name:string;insulin_type:string;dose_units:string;injection_site:string;administered_at:string};
export type Meal = {id:string;meal_name:string;meal_type:string;carbohydrates_grams:string;consumed_at:string};
export type Reminder = {id:string;title:string;reminder_type:string;reminder_time:string;timezone:string;enabled:boolean};
export type Dashboard = {latest_glucose:Glucose|null;last_insulin:Insulin|null;today_insulin_units:number;today_carbohydrates_grams:number;recent_glucose:Glucose[];reminders:Reminder[];as_of:string};
