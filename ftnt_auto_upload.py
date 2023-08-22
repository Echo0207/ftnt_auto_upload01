from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
import os
import threading
import pysftp
import tarfile
from datetime import datetime, timedelta
import time
import re
import shutil
import fnmatch
import xml.etree.ElementTree as ET
import requests
from collections import OrderedDict, deque
import xml.etree.ElementTree as ET
import tarfile
import json

class ProcessedFilesList:
    def __init__(self, filename="processed_files.txt"):
        self.filename = filename

        if not os.path.exists(self.filename):
            with open(self.filename, "w") as f:
                pass

    def add(self, file_name):
        with open(self.filename, "a") as f:
            f.write(file_name + "\n")

    def get_all(self):
        with open(self.filename, "r") as f:
            return f.read().splitlines()

def check_missed_files(directory):
    processed_files = ProcessedFilesList()
    
    all_files = set(os.listdir(directory))
    processed = set(processed_files.get_all())
    missed_files = all_files - processed

    for file in missed_files:
        process_missed_file(os.path.join(directory, file))
        processed_files.add(file)

def process_missed_file(file_path):
    try:
        CheckCustomerStatus(file_path)
    except Exception as e:
        os.remove(file_path)



def format_date(dt):
    # 提取年月日
    year, month, day = dt.year, dt.month, dt.day
    # 去掉月份前导零
    if month < 10:
        month = str(month).strip('0')
    else:
        month = str(month)

    # 去掉日期前导零
    if day < 10:
        day = str(day).strip('0')
    else:
        day = str(day)

    # 格式化日期字符串
    return f"{year}-{month}-{day}"
# 取得當天日期
#today = datetime.today().strftime('%Y-%m-%d').lstrip('0')
today = datetime.today()
today = format_date(today)
now = datetime.now()

# 設定log檔案路徑，檔名以當天日期命名
barcode_log ='D:/python/ftnt_download_log/logs'
log_file_path = f'D:/python/ftnt_download_log/logs/{today}/sftp_download_{today}.log'
extractfile_originale_log =f'D:/python/ftnt_download_log/logs/{today}/original_log'
backup_log_include_directory_tgz =f'D:/python/ftnt_download_log/logs/{today}/backup_log'
fail_log_directory =f'D:/python/ftnt_download_log/logs/fail_log/{today}'
configfileName = "D:/python/ftnt_download_log/config.xml"
record_Barcode_file = f'D:/python/ftnt_download_log/logs'
Ftnt_QA_Check_directory=f'D:/python/ftnt_download_log/logs/QA_Check'
WEVSERVICEURL ="http://172.16.0.84/mes.wip.webservice/ftservice.asmx"
QAWEBSERVICEURL ="http://172.16.0.84/mes.wip.webservice/QA_BARCODE.asmx"
CustomerAPI ="http://172.22.50.6/fldb/GetUnitInfo/"
xml_file_path = r'D:/python/ftnt_download_log/SampleSuccessLog.xml'
# 確認log檔案的目錄是否存在，不存在則建立目錄

def is_new_day(current_day):
    new_day = datetime.today()
    new_day = format_date(new_day)
    return new_day != current_day

def CreateFile():
    global today, extractfile_originale_log, backup_log_include_directory_tgz, log_file_path, fail_log_directory, Ftnt_QA_Check_directory
    today = datetime.today()
    today = format_date(today)
    log_dir = os.path.dirname(f'D:/python/ftnt_download_log/logs/{today}')
    try:
        if not os.path.exists(extractfile_originale_log):
            os.makedirs(extractfile_originale_log)
            os.chmod(extractfile_originale_log, 0o777)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            os.chmod(log_dir, 0o777)
        if not os.path.exists(log_file_path):
            os.makedirs(log_file_path)
        if not os.path.exists(backup_log_include_directory_tgz):
            os.makedirs(backup_log_include_directory_tgz)
        if not os.path.exists(fail_log_directory):
            os.makedirs(fail_log_directory)
        if not os.path.exists(Ftnt_QA_Check_directory):
            os.makedirs(Ftnt_QA_Check_directory)
    except FileNotFoundError as e:
        print("Error creating log file:", e)
#num_threads =3
#file_queue = queue.Queue()
# 設定連接SFTP的相關資訊
host = '172.22.50.13'
username = 'sftp_cm'
password = '7/$mPq429btK?vKx'
port = 22
# 設定從SFTP下載的資料夾名稱
remote_folder = '/log_store/cm_sftp'
# 設定從SFTP下載的資料夾內檔案的時間限制，例如最新的5分鐘內產生的檔案
# 建立SFTP連接
cnopts = pysftp.CnOpts()
cnopts.hostkeys = None
sftp = pysftp.Connection(host=host, username=username, password=password, port=port, cnopts=cnopts)
#從SFTP 下載資料
def download_and_extract():
    log("download_and_extract有執行")
    try:
        time_limit = datetime.now() - timedelta(seconds=10)
        # 進入SFTP資料夾
        with sftp.cd(remote_folder):
            # 取得資料夾中的所有檔案列表
            remote_files = sftp.listdir()
            # 找出最新的檔案
            newest_file = []
            for f in remote_files:
                # 比較檔案修改時間是否在時間限制之內
                if re.match(today, f):
                    # 取得檔案的修改時間
                    mtime = sftp.stat(f).st_mtime
                    if datetime.fromtimestamp(mtime) >= time_limit:
                        remote_path = f"{remote_folder}/{f}"
                        if len(newest_file)==0:
                            newest_file.append(f)
                        else:
                            newest_file.append(f)
        # 下載最新的檔案到本機資料夾
            if len(newest_file)!=0:
                for item in newest_file:
                    remote_path = f"{remote_folder}/{item}"
                    local_path = barcode_log+f'/{today}'
                    local_path = os.path.join(local_path, item)
                    local_path= local_path.replace('\\', '/')
                    sftp.get(remote_path, local_path)
                    extractfile(local_path,item)
                    os.remove(local_path)
                    log(item)
            else:
                log("NO File")
        time_limit = datetime.now() - timedelta(hours=1)
        # 進入SFTP資料夾
        with sftp.cd(remote_folder):
            # 取得資料夾中的所有檔案列表
            remote_files = sftp.listdir()
            # 找出最新的檔案
            newest_file = []
            for f in remote_files:
                # 比較檔案修改時間是否在時間限制之內
                if re.match(today, f):
                    # 取得檔案的修改時間
                    mtime = sftp.stat(f).st_mtime
                    if datetime.fromtimestamp(mtime) >= time_limit:
                        remote_path = f"{remote_folder}/{f}"
                        if len(newest_file)==0:
                            newest_file.append(f)
                        else:
                            newest_file.append(f)
        # 下載最新的檔案到本機資料夾
            if len(newest_file)!=0:
                for item in newest_file:
                    remote_path = f"{remote_folder}/{item}"
                    local_path = barcode_log+f'/{today}'
                    local_path = os.path.join(local_path, item)
                    local_path= local_path.replace('\\', '/')
                    sftp.get(remote_path, local_path)
                    extractfile(local_path,item)
                    os.remove(local_path)
                    log(item)
            else:
                log("NO File")
    except Exception as e:
        log("download_and_extract Exception:"+e)
        pass    
# 解壓縮下載的檔案
def extractfile(local_path,item):
    try:
        with tarfile.open(local_path, "r:gz") as tar:
            tar.extractall(extractfile_originale_log)
    except Exception as e:
	    log("extractfile:"+e)    
# 寫log
def log(message):
    global today
    CreateFile()
    now = datetime.now()
    try:
        with open(f'D:/python/ftnt_download_log/logs/{today}/{today}.log', 'a') as f:
            f.write(now.strftime("%Y-%m-%d %H:%M:%S")+' '+ str(message) + '\n')  
        print(now.strftime("%Y-%m-%d %H:%M:%S")+' '+ str(message) + '\n')  
    except FileNotFoundError as e:
        print("Error creating log file:", e)     
#讀取設定檔
def ReadSettingXml(configfile):
  tree = ET.parse(configfile)
  root = tree.getroot()
#找主資料夾
def finddirs(n, path):
    os.environ['n'] = str(n)
    os.environ['path'] = path
    dirtemp =[]
    for root, dirs, files in os.walk(path):
        depth = root[len(path) + len(os.sep):].count(os.sep) + 1  # 計算目前遍歷深度
    # 如果目前遍歷深度小於等於最大遍歷深度，則處理當前目錄下的檔案和資料夾
        search_str = ["FG"]
        ext = [".xml"]
        if depth <= n:
            for file in files:
                for s in search_str:
                    if fnmatch.fnmatch(file, f"*{s}*"):
                        for e in ext:
                            if s in file and file.endswith(e):
                                dirtemp.append(os.path.join(root, file))
    return dirtemp
#移動log
def copylogfile(source, dest):
    try:
        filename = os.path.basename(source)
        if os.path.exists(os.path.join(dest,filename)):
            os.remove(os.path.join(dest,filename))
        shutil.move(source, dest)
    except Exception as e:
        log("copylogfile Exception:"+e)
#讀取設定檔
def ReadSettingXml(configxml,node):
    try:
        tree = ET.parse(configxml)
        root = tree.getroot()
        stationid =[]
        confignode =node
        for child in root.iter():
            if(child.tag ==confignode):
                stationid.append(child.text)
                return stationid
    except ET.ParseError as e:
        log("\033[31mFormat Error: {} in {}.\033[0m".format(e, configxml))
def clean_invalid_xml_chars(xml_string):
    # Define the regex pattern for valid XML characters
    valid_xml_chars_pattern = re.compile(
        u"[\u0009\u000A\u000D\u0020-\uD7FF\uE000-\uFFFD\U00010000-\U0010FFFF]+"
    )

    # Use regex to find all valid XML characters and join them
    cleaned_xml_string = "".join(valid_xml_chars_pattern.findall(xml_string))

    return cleaned_xml_string
#分析log檔執行目的
def CheckRunPurpose(fntxml):
	with open(fntxml, "r", encoding="utf-8") as file:
		xml_data = file.read()
	cleaned_xml_data = clean_invalid_xml_chars(xml_data)
	with open(fntxml, "w", encoding="utf-8") as file:
		file.write(cleaned_xml_data)
	runpurpose = ReadSettingXml(fntxml,'RunPurpose')
	if runpurpose[0] == 'Product':
		return 1
	else:
		filename = os.path.basename(fntxml)
		if os.path.exists(os.path.join(Ftnt_QA_Check_directory,filename)):
			os.remove(os.path.join(Ftnt_QA_Check_directory,filename))
		shutil.move(fntxml,Ftnt_QA_Check_directory)
		log(runpurpose[0])
		return 0
#解析xml
def Parse(xml):
	try:
		tree = ET.parse(xml)
		return tree
	except IOError as e:
		log("Error: {}".format(e))
	except ET.ParseError as e:
		log("\033[31mFormat Error: {} in {}.\033[0m".format(e, xml))

def DeleteBlank(text):
	return text.replace('\n', "").replace('\t', '').replace('\r', '')\
		.replace('>', '').replace("<", '') 
def Uploadxml(strings="", ulxmlfile="", args0='MBTestXml?sXML=', args1='sXML'):
	URL = 'http://172.16.0.84/MES.WIP.WebService/FTService.asmx/{}'.format(
		args0)
	if ulxmlfile != "":
		with open(ulxmlfile, 'rt') as f:
			strings = f.read()
	try:
        # 定義最大重試次數
		max_retries = 3
		callwebserviceURL =WEVSERVICEURL+"/MBTestXml"
		payload= {'sXML':strings}
		for retry in range(max_retries):
			response = requests.post(callwebserviceURL, data=payload)
            # 如果收到了正確的回應，就跳出迴圈
			if response.status_code == 200:
				break
            # 如果收到了錯誤的回應，就等待一段時間後重試
			print(ET.fromstring(response.text).text)
			log(f'Received error status code {response.status_code}, retrying in 5 seconds...')
			time.sleep(3)
        # 處理回應數據
		if response.status_code == 200:
			finaltest=ET.fromstring(response.text).text
		else:
			fsn =None
	except Exception as e:
		log("Uploadxml Exception:"+e)
	return finaltest

def UploadXmlBack(strings="", content="", args0='MBTestXml?sXML=', args1='sXML'):
	URL = 'http://172.16.0.84/MES.WIP.WebService/FTService.asmx/{}'.format(
		args0)
	try:
        # 定義最大重試次數
		max_retries = 3
		callwebserviceURL =WEVSERVICEURL+"/MBTestXml"
		payload= {'sXML':content}
		for retry in range(max_retries):
			response = requests.post(callwebserviceURL, data=payload)
            # 如果收到了正確的回應，就跳出迴圈
			if response.status_code == 200:
				break
            # 如果收到了錯誤的回應，就等待一段時間後重試
			print(ET.fromstring(response.text).text)
			log(f'Received error status code {response.status_code}, retrying in 5 seconds...')
			time.sleep(3)
        # 處理回應數據
		if response.status_code == 200:
			finaltest=ET.fromstring(response.text).text
		else:
			fsn =None
	except Exception as e:
		log("Uploadxml Exception:"+e)
	return finaltest

def CreateAllxmlandUpload(fntxml, ctree):
	try:
		ftree = ET.parse(fntxml)
		log("Fortinet XML name:{}\n".format(fntxml))
	except ET.ParseError as e:
		log("\033[31mFormat Error: {} in {}.\033[0m".format(e, fntxml))
	TestMachine = ftree.find(".//Name").text
	for dut in ftree.findall(".//DUT"):
		Uxmlname = CreateSingleUploadXml(dut, ctree, TestMachine)
		#os.system("clear")
		log("Start Upload Test Result... ")
		finXml =ET.parse(Uxmlname)
		BarcodeNO= finXml.find(".//BarcodeNo").text
		Umesg = Uploadxml(ulxmlfile=Uxmlname)
		FtntSnFile =barcode_log+os.sep+BarcodeNO
		if not os.path.exists(FtntSnFile):
			os.makedirs(FtntSnFile)
		if "OK" in Umesg:
			log("Upload BarcodeNO :{} MES Status:{} To Ftnt Directory {}".format(BarcodeNO,Umesg,FtntSnFile))
			if(os.path.exists(os.path.join(FtntSnFile,Uxmlname))):
				os.remove(os.path.join(FtntSnFile,Uxmlname))
			shutil.move(Uxmlname,FtntSnFile)
		else:
			log("Upload BarcodeNO :{} MES Status FAIL:{}".format(BarcodeNO,Umesg,FtntSnFile))
			CheckCustomerStation("Upload BarcodeNO :{} MES Status FAIL:{}，Fail_Log{}".format(BarcodeNO,Umesg,FtntSnFile),Uxmlname,ctree)
		shutil.move(Uxmlname,fail_log_directory)			
		log("-----------------------------")
		log("")

def ReadSettingXmlSub(configxml, node):
    try:
        tree = ET.parse(configxml)
        root = tree.getroot()

        confignode = node
        child_data = {}

        # Find the specified node (confignode) and iterate over its children
        for child in root.iter(confignode):
            for subchild in child:
                child_data[subchild.tag] = subchild.text

        return child_data

    except ET.ParseError as e:
        log("\033[31mFormat Error: {} in {}.\033[0m".format(e, configxml))

def Strip(text):
	return text.strip("\n").strip()

def compare_stations(station1, station2, station_order):
    return station_order.index(station1) - station_order.index(station2)

def get_next_station(current_station, ConventStation, station_comparison):
    current_index = ConventStation.index(current_station)
    next_index = current_index + station_comparison
    if next_index < len(ConventStation):
        return ConventStation[next_index]
    else:
        return "N/A"

def CheckCustomerStation(Umesg,ftntfailLog,ctree):
    try:
        patterns = {
            'barcode': r'BarcodeNO\s*:\s*(\w+)',
            'next_station': r'Next Station:([\w\s-]+)',
            'current_station': r'(?:Current Station:([\w/-]+)|Barcode\s*Current([\w\(\)/\s,]+))'
        }
        extracted_info = {}
        for key, pattern in patterns.items():
            match = re.search(pattern, Umesg)
            extracted_info[key] = match.group(1) if match else "N/A"
        # 打印提取到的信息
        print(f"Barcode: {extracted_info['barcode']}")
        print(f"Next Station: {extracted_info['next_station']}")
        print(f"Current Station: {extracted_info['current_station']}")
        xml_string = read_xml_file(xml_file_path)
        if extracted_info['next_station'] =='SFC-功能':
            extracted_info['next_station'] ="SFC-TEST"
        if extracted_info['current_station'] =='SFC-功能':
            extracted_info['current_station'] ="SFC-TEST"
        ConventStation =['SFC-BIOS','SFC-OS','SFC-TEST'] 
        station_comparison = compare_stations(extracted_info['current_station'], extracted_info['next_station'], ConventStation)
        if station_comparison > 0:
            xmlpatterns = {
                'TestStation': r"<TestStation>(.*?)</TestStation>",
                'TestMachine': r"<TestMachine>(.*?)</TestMachine>",
                'Tester': r"<Tester>(.*?)</Tester>",
                'BarcodeNo': r"<BarcodeNo>(.*?)</BarcodeNo>"
            }

            with open(ftntfailLog, 'rt') as f:
                ftntfailLog_strings = f.read()

            with open(xml_file_path, 'rt') as f:
                xml_file_path_strings = f.read()

            for i in range(station_comparison):
                for key, pattern in xmlpatterns.items():
                    xmlmatch = re.search(pattern, ftntfailLog_strings)
                    old_value = xmlmatch.group(1) if xmlmatch else "N/A"
                    if key == 'TestStation':
                        old_value = ctree.find(".//{}".format(extracted_info['next_station'])).text
                    xml_file_path_strings = re.sub(pattern, f"<{key}>{old_value}</{key}>", xml_file_path_strings)

                UploadXmlBack(content=xml_file_path_strings)
                log(f"補上傳站別{extracted_info['next_station']}:{xml_file_path_strings}")

                # 更新 next_station 为迭代后的站点
                extracted_info['next_station'] = get_next_station(extracted_info['current_station'], ConventStation, station_comparison)

            UploadXmlBack(content=ftntfailLog_strings)
            log(f"原始上傳站別 {extracted_info['current_station']}:{ftntfailLog_strings}")

        else:
            pass
    except Exception as e:
        shutil.move(ftntfailLog,fail_log_directory)
        log("CheckCustomerStation"+e)
        
    
def read_xml_file(file_path):
    # 解析XML檔案
    tree = ET.parse(file_path)
    # 獲取根元素
    root = tree.getroot()
    # 將根元素轉換成字串
    xml_string = ET.tostring(root, encoding='unicode')
    return xml_string

def CreateTestitemPassdict(dutobj, xpath):
	passinfo = OrderedDict()
	for i in dutobj.iter(xpath):
		for i in i.iter():
			if i.text != None and Strip(i.text) != '':
				if "SN" in xpath:
					passinfo.update({"FNT_SN": i.text})
				elif "MacAddress" in xpath:
					passinfo.update({"MAC": i.text.replace(":", '').upper()})
				else:
					passinfo.update({i.tag: i.text})
	return passinfo

def CreateTestitemErrdict(dutobj, xpath):
	errinfo = OrderedDict()
	names = deque(maxlen=2)
	NgItem = ""
	for i in dutobj.iter(xpath):
		for i in i.iter():
			if i.text != None and Strip(i.text) != "":
				names.append(i.text)
				if i.text == "Failed" or i.text == 'Aborted':
					NgItem = names[0]
					errinfo.update({"FNT_TESTFAILITEM": names[0]})
				if "Error_Code" in i.tag:
					errinfo.update({"FNT_ERRCODE": DeleteBlank(i.text)})
				if "Error_Category" in i.tag:
					errinfo.update({"FNT_ERRCATEGORY": DeleteBlank(i.text)})
				if "Error_messsage" in i.tag:
					errinfo.update({"FNT_ERRMESG": DeleteBlank(i.text)})
			else:
				if "Error_messsage" in i.tag:
					errinfo.update({"FNT_ERRMESG": 'There are 0 alert console messages'})
	return errinfo, NgItem

def CreateNode(tag, attrib={}, text=None):
	element = ET.Element(tag, attrib)
	element.text = text
	return element

def AddNode(parentobj, childobj):
	parentobj.append(childobj)

def CreateTestitemAttrib(value):
	return ({"Key": value})

def ConventSn(fsn):
    try:
        # 定義最大重試次數
        max_retries = 3
        callwebserviceURL =WEVSERVICEURL+"/GetBarcodeByComponent"
        payload= {'sComponentNo':fsn}
        for retry in range(max_retries):
            response = requests.post(callwebserviceURL, data=payload)
            # 如果收到了正確的回應，就跳出迴圈
            if response.status_code == 200:
                break
            # 如果收到了錯誤的回應，就等待一段時間後重試
            log(f'Received error status code {response.status_code}, retrying in 5 seconds...')
            time.sleep(3)
        # 處理回應數據
        if response.status_code == 200:
            finaltest=ET.fromstring(response.text).text
            if finaltest =='Can not find the barcode!':
                fsn ='Can not find the barcode!'
            elif len(finaltest)>10 and len(finaltest)<18:
                fsn=fsn
            else:
                fsn =finaltest
        else:
            fsn =None
        return fsn
    except Exception as e:
        log("ConventSn Exception"+e)

def WriteXml(filename, root):
    ctree = ET.ElementTree(root)
    ctree.write(filename, xml_declaration=True, encoding='utf-8')

def CreateSingleUploadXml(dutobj, ctree, TestMachine):
	# Declare TestInfo mesg
    # Add TestItem EMM_GROUPNO
	itemdict = OrderedDict()
	itemdict_Sn = CreateTestitemPassdict(dutobj, 'SN')
	itemdict_Mac = CreateTestitemPassdict(dutobj, 'MacAddress')
	itemdict_Bom = CreateTestitemPassdict(dutobj, 'BOM')
	itemdict_Err, NgItem = CreateTestitemErrdict(dutobj, 'Tests')
	# get Device, scriptversion, test duration
	itemdict_Testconfig = CreateTestitemPassdict(dutobj, "TestConfig")
	# Get Tester
	tester = dutobj.find(".//OPID").text
	if tester != None and Strip(tester):
		Tester = tester.replace("OP", '')
	else:
		Tester = "1"
	# create root
	root = CreateNode("root")
    
	# create root's childs node
	childs_1 = ["TestStation", "TestMachine", "Tester", "BarcodeNo",
				"TestStatus", "Customer", "TestTime", "TestInfo", "NgInfo"]
    
	# create childs node
	childs_1s_text = []
	TestStation = dutobj.find(".//TestStation").text
	childs_1s_text.append(ctree.find(".//{}".format(TestStation)).text)
	childs_1s_text.append(TestMachine)
	childs_1s_text.append(Tester)
	childs_1s_text.append(ConventSn(itemdict_Sn['FNT_SN']))
	Status = "P" if dutobj.find(".//FinalResult").text == "PASS"else "F"
	childs_1s_text.append(Status)
	childs_1s_text.append("")
	childs_1s_text.append(dutobj.find(".//EndTime").text)
	childs_1s_text.append("")
	childs_1s_text.append("")
    
	# create root's childs
	for elem, txt in zip(childs_1, childs_1s_text):
		element = CreateNode(elem, text=txt)
		if elem == "TestInfo":
			TestInfo = element
		if elem == "NgInfo":
			NgInfo = element
		AddNode(root, element)

    # Find barcode_emm_directory
	barcode_emm_directory = find_sn_emm_line_xml(ConventSn(itemdict_Sn['FNT_SN']))
	if barcode_emm_directory !=None:
		expand_data = ReadSettingXmlSub(barcode_emm_directory,'Expand')
	else:
		expand_data = {}

	# create testinfo msg
	# Ordered
	[itemdict.update({x: y}) for x, y in itemdict_Sn.items()]
	[itemdict.update({x: y}) for x, y in itemdict_Testconfig.items()]
	[itemdict.update({x: y}) for x, y in itemdict_Mac.items()]
	[itemdict.update({x: y}) for x, y in itemdict_Bom.items()]
	[itemdict.update({x: y}) for x, y in itemdict_Err.items()]

	# create TestItem Nodes
	for idx, ikey in enumerate(itemdict.keys()):
		attribute = CreateTestitemAttrib(ikey)
		TestItem = CreateNode("TestItem", attribute, itemdict.get(ikey))
		AddNode(TestInfo, TestItem)
    
	if expand_data:
		# Add nodes for expand_data after adding all other TestItems
		for key, value in expand_data.items():
			lineattribute = CreateTestitemAttrib(key)
			expand_node = CreateNode("TestItem", lineattribute, value)
			AddNode(TestInfo, expand_node)
        
        # create ngnifo msg
	ngnodes = ["Errcode", "Pin", "Location"]
	for ngelem in ngnodes:
		ngelement = CreateNode(ngelem)
		if ngelem == "Errcode" and NgItem != "":
			try:
				ngelement.text = ctree.find(".//_{}".format(NgItem)).get("Errcode")
			except AttributeError as e:
				log("Check Test Item in Config File")
		AddNode(NgInfo, ngelement)

	# Write Uploadxml
	ctime = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
	WriteXml("{}_{}_{}.xml".format(
		itemdict_Sn['FNT_SN'], TestStation, ctime), root)
	return "{}_{}_{}.xml".format(itemdict_Sn['FNT_SN'], TestStation, ctime)
def find_sn_emm_line_xml(sn):
    sn_folder_path = os.path.join(record_Barcode_file, sn)
    if os.path.exists(sn_folder_path):
        for dirpath, dirnames, filenames in os.walk(sn_folder_path):
            for filename in filenames:
                if filename == f'{sn}_emm_line.xml':
                    return os.path.join(dirpath, filename)
    return None
def UploadFTNTApproveXml(barcodeno):
    callwebserviceurl =QAWEBSERVICEURL+'/InsertQABarcodeUpload'
    payload = {'sBarcodeNo':barcodeno,'sDateTime':today}
    try:
        max_retries = 3
        for retry in range(max_retries):
            response = requests.post(callwebserviceurl, data=payload)
            # 如果收到了正確的回應，就跳出迴圈
            if response.status_code == 200:
                break
            # 如果收到了錯誤的回應，就等待一段時間後重試
            print(ET.fromstring(response.text).text)
            log(f'Received error status code {response.status_code}, retrying in 3 seconds...')
            time.sleep(3)
    except Exception as e:
        log("UploadFTNTApproveXml"+e)
    return ET.fromstring(response.text).text
def GetFtntBarcode(file,ctree=None):
    try:
        if ctree is None:
            ctree = Parse(configfileName)
        ftree = ET.parse(file)
        for FtntSn in ftree.findall(".//SN"):
            FtntStation =ftree.find(".//TestStation")
            ConventStation =['SMCS'] 
            if FtntStation.text in ConventStation:
                FtntSn=ConventSn(FtntSn.text)
            else:
                FtntSn =FtntSn.text
            if FtntSn == None or FtntSn =='Can not find the barcode!':
                os.remove(file)
            else :
                CreateAllxmlandUpload(file,ctree)
                FtntSnFile =barcode_log+os.sep+FtntSn
                if not os.path.exists(FtntSnFile):
                    os.makedirs(FtntSnFile)
                filename = os.path.basename(file)
                if(os.path.exists(os.path.join(FtntSnFile,filename))):
                    os.remove(os.path.join(FtntSnFile,filename))
                shutil.move(file,FtntSnFile)
    except Exception as e:
        os.remove(file)
        log("GetFtntBarcode Exception"+e)
        
        pass
def CallCustomerAPI(FtntSn):
    callAPIurl = CustomerAPI+FtntSn
    payload= {}
    r = requests.get(callAPIurl,data=payload)
    if(r.status_code ==200):
        print(r.text)
        data = json.loads(r.text)
    return data
def CheckCustomerStatus(fntxml):
    try:
        ftree = ET.parse(fntxml)
        for FtntSn in ftree.findall(".//SN"):
            FtntStation =ftree.find(".//TestStation")
            ConventStation =['SMCS'] 
            if FtntStation.text in ConventStation:
                FtntSn=ConventSn(FtntSn.text)
            else:
                FtntSn =FtntSn.text
            if FtntSn == None or FtntSn =='Can not find the barcode!' or len(FtntSn)<=10:
                os.remove(fntxml)
            else:
                pass
                '''data =CallCustomerAPI(FtntSn)
                quarantine_msg = data[0]['quarantine_msg']
                status = data[0]['status']
                if quarantine_msg:
                    pass
                else:
                    pass
                if status =="Test not completed":
                    os.remove(fntxml)'''
                #else:
                #    UploadFTNTApproveXml(FtntSn)
    except Exception as e:
        log("CheckCustomerStatus Exception"+e)
        os.remove(fntxml)
        pass
def UploadTOMes():
    log("UploadTOMes有執行")
    try:
        logpath = extractfile_originale_log+"/var/log/bit_pro" #(Must be copied log file path)
        if len(logpath) !=0 :
            dest = extractfile_originale_log+"/dest"
            if not os.path.exists(dest):
                os.makedirs(dest)
            ndays = 1
            flag = 1
            if flag ==1:
                for x in finddirs(ndays, logpath):
                    copylogfile(x, dest)
                    dir_path = os.path.dirname(x)
                    shutil.rmtree(dir_path)
            inpath = dest
            files = []
            
            for root, dirs, filenames in os.walk(inpath):
                for filename in filenames:
                    path = os.path.join(root, filename)
                    files.append(path)
            if len(files) == 0:
                pass
            else:
                for fntxml in files:
                    if CheckRunPurpose(fntxml):
                        #GetFtntBarcode(fntxml,ctree)
                        with ThreadPoolExecutor(max_workers=4) as executor:
                            # 提交要執行的任務
                            executor.submit(GetFtntBarcode,fntxml) 
                    else :
                        pass
        else:
            log("UploadTOMes NO File")
            pass
    except Exception as e:
        log("UploadTOMes Exception:"+e)
        pass

def main():
    log('Run Start')
    try:
        process_tasks()  

        if len(Ftnt_QA_Check_directory) != 0:
            inpath = Ftnt_QA_Check_directory
            files = []

            for root, dirs, filenames in os.walk(inpath):
                for filename in filenames:
                    path = os.path.join(root, filename)
                    files.append(path)

            if len(files) > 0:
                for fntxml in files:
                    try:
                        CheckCustomerStatus(fntxml)
                    except Exception as e:
                        os.remove(fntxml)

        # 在結尾處檢查遺漏的檔案
        check_missed_files(Ftnt_QA_Check_directory)

    except Exception as e:
        log("main:" + str(e))
    print("main() 函数执行完成")
    log('Run End')



# 新增 process_tasks() 函数
def process_tasks():
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        tasks = [executor.submit(UploadTOMes), executor.submit(download_and_extract), executor.submit(download_and_extractHours)]
        #tasks = [executor.submit(UploadTOMes)]
        for future in concurrent.futures.as_completed(tasks):
            try:
                result = future.result()
            except Exception as e:
                log("process_tasks Exception:"+e)
                print(f"任务产生了一个异常: {e}")  
executorMain = concurrent.futures.ThreadPoolExecutor(max_workers=5)

def run_threaded():
    global executorMain,today
    future = executorMain.submit(main)
    try:
        result = future.result(timeout=20)
    except concurrent.futures.TimeoutError:
        for futures in concurrent.futures.as_completed([future]):
            futures.cancel()
        executorMain = concurrent.futures.ThreadPoolExecutor(max_workers=5)
    
if __name__ == '__main__':
    process_tasks()
    while True:
        run_threaded()   # 调用 main() 函数
        time.sleep(1)
        