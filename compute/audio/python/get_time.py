import cv2
import re
import pytz
import pytesseract
from datetime import datetime,timedelta


def get_timestamp(frame):

      gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
      cropped_image=gray[80:150,3000:3800]
      cropped_image=cv2.resize(cropped_image,(800,100))
      binary = cv2.adaptiveThreshold(cropped_image,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,11,60)
      text = pytesseract.image_to_string(binary,config='--psm 13  -c tessedit_char_whitelist=:-0123456789APM" " ')
      return text;


def convert24hour(hour,PM_time):
    if  not PM_time and hour==12:
        return 0;
    if  PM_time and hour!=12:
        return hour+12
    else:
        return hour

def convert_to_UTC(date,time):
    str_time=str(time)
    dt=date+' '+str_time
    D=datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
    timezone = pytz.timezone('America/New_York')
    t=timezone.localize(D)
    UTC=t.astimezone(pytz.utc)
    date=str(UTC.date())
    time=timedelta(hours=UTC.hour,minutes=UTC.minute,seconds=UTC.second)
    return(date,time)

### NOTE-: if AM and PM is not present in timestamp , by default PM
def clean_OCR_Time(OCR_time):
   ## split the time-date
   split=OCR_time.split(' ')
   ## save time
   time=split[1]
   time_format=''
   ## 0 means PM is not present in the OCR time
   ## 1 means PM is present in the OCR time 
   PM_time=1;
   if len(split)>2 and split[2]=='AM':
       PM_time=0
   
   ## extract unenecessary char 
   for num,ix in enumerate(time):
     if ix.isdigit() or ix==':' :
        time_format=time_format+ix        

   ## use regx to further clean extraction
   p = re.compile('\d{1,2}')
   time_format=p.findall(time_format)
   ## some error with extraction 

   if (len(time_format)<3):
      return None;
   
   ## convert string to datetime with error_handling                    
   hour_OCR=int(time_format[0])
   hour_OCR=convert24hour(hour_OCR,PM_time);
   if hour_OCR>24:
      return None;
   Min_OCR=int(time_format[1])
   if Min_OCR>60:
        return None;
   sec_OCR=int(time_format[2])
   if sec_OCR>60:
        sec_OCR=0;
   time_OCR=timedelta(hours=hour_OCR,minutes=Min_OCR,seconds=sec_OCR)
   return (split[0],time_OCR)

def extract_date(video):
   split=video.split('/')
   video_name=''
   for File in split:
      if File.find('.avi') != -1:
        video_name=File
        break;
   name_list=video_name.split('_')
   date_time=''
   for ix in name_list[4]:
      if ix.isdigit():
            date_time=date_time+ix
   year=date_time[:4]
   month=date_time[4:6]
   day=date_time[6:8]
   date=year+'-'+month+'-'+day
   hour=int(date_time[8:10])
   Min=int(date_time[10:12])
   time_delta= timedelta(hours=hour,minutes=Min)
   return (date,time_delta)


def extract_time(video,ocr_bool,file_bool,log):
   
   print(pytesseract.get_tesseract_version())
   threshold_error=timedelta(hours=1,minutes=0)
   ocr_time_failed=False;
   file_time_failed=False;
   file_name_time=None;
   file_name_date=None;
   default_time=timedelta(hours=9,minutes=0)
   default_date="2020-05-28"
    
   try: 
     file_name_date,file_name_time=extract_date(video)
   except Exception as e:
       log.write("ERROR in extracting the date-time from the file_name\n")
       log.write(f"{e}\n")
       file_time_failed=True;

   try:
      video_object=cv2.VideoCapture(video)
      ret,frame=video_object.read()
      ocr_time_stamp=get_timestamp(frame)
      ocr_date,ocr_time=clean_OCR_Time(ocr_time_stamp)
   except Exception as e:
       log.write("ERROR in extracting the date-time from the OCR\n")
       log.write(f"{e}\n")
       ocr_time_failed=True;

   if(file_time_failed and ocr_time_failed):
       log.write(f"Using a default time_stamp {default_date}T{str(default_time)}\n")
       return (default_date,default_time)

   elif ocr_time_failed and ocr_bool == False:
       log.write(f"Using file extracted time_stamp {file_name_date}T{str(file_name_time)}\n")
       file_name_date,file_name_time=convert_to_UTC(file_name_date,file_name_time)
       return(file_name_date,file_name_time)
       
   elif file_time_failed and file_bool == False:
       log.write(f"Using OCR extracted time_stamp and OCR date {ocr_date}T{str(ocr_time)}\n")
       ocr_date,ocr_time=convert_to_UTC(ocr_date,ocr_time)
       return(ocr_date,ocr_time)

   else:
       if abs(ocr_time-file_name_time) < threshold_error or ocr_bool == True :
           log.write(f"Using OCR timestamp {file_name_date}T{str(ocr_time)}\n")
           file_name_date,ocr_time=convert_to_UTC(file_name_date,ocr_time)
           return(file_name_date,ocr_time)
       else:
           log.write(f"Using file_name timestamp {file_name_date}T{str(file_name_time)}\n")
           file_name_date,file_name_time=convert_to_UTC(file_name_date,file_name_time)
           return(file_name_date,file_name_time)



