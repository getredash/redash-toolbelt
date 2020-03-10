from datetime import datetime, timedelta
from collections import namedtuple


def get_frontend_vals():
	'''Returns a named tuple of dynamic date ranges that match Redash's front-end
	'''

	ranges = calculate_ranges()
	singles = calculate_singletons()

	valkeys = [k for k in ranges.keys()] + [k for k in singles.keys()]

	Values = namedtuple('Values', ' '.join(valkeys))

	return Values(**ranges, **singles)

def calculate_ranges():

	# SuperToday is more specific than datetime.datetime.today
	SuperToday = namedtuple('SuperToday', 'month day year weeknum weekday')
	DateRange = namedtuple('DateRange', 'start end')

	today = datetime.today()
	_ymd = (today.month, today.day)

	t = SuperToday(*_ymd, *today.isocalendar())

	ranges = {}

	#  _____ _     _      __        __        _     
	# |_   _| |__ (_)___  \ \      / /__  ___| | __ 
	#   | | | '_ \| / __|  \ \ /\ / / _ \/ _ \ |/ / 
	#   | | | | | | \__ \   \ V  V /  __/  __/   <  
	#   |_| |_| |_|_|___/    \_/\_/ \___|\___|_|\_\ 

	start = datetime.strptime(f"{t.year}-{t.weeknum}-1", '%G-%V-%u')
	end = start + timedelta(days=6)

	ranges['d_this_week'] = DateRange(start,end)

											
	#  _____ _     _       __  __             _   _      
	# |_   _| |__ (_)___  |  \/  | ___  _ __ | |_| |__   
	#   | | | '_ \| / __| | |\/| |/ _ \| '_ \| __| '_ \  
	#   | | | | | | \__ \ | |  | | (_) | | | | |_| | | | 
	#   |_| |_| |_|_|___/ |_|  |_|\___/|_| |_|\__|_| |_| 

	start = datetime.strptime(f"{t.year}-{t.month}-1", '%Y-%m-%d')
	e_year, e_month = (t.year,t.month+1) if t.month < 12 else (t.year+1,1)
	end = datetime.strptime(
		f"{e_year}-{e_month}-1", '%Y-%m-%d') \
		- timedelta(days=1)

	ranges['d_this_month'] = DateRange(start,end)
											  
	#  _____ _     _      __   __                    
	# |_   _| |__ (_)___  \ \ / /__  __ _ _ __       
	#   | | | '_ \| / __|  \ V / _ \/ _` | '__|      
	#   | | | | | | \__ \   | |  __/ (_| | |         
	#   |_| |_| |_|_|___/   |_|\___|\__,_|_|         

	start = datetime.strptime(f"{t.year}-1-1", '%Y-%m-%d')
	end = datetime.strptime(f"{t.year}-12-31", '%Y-%m-%d')

	ranges['d_this_year'] = DateRange(start,end)

												  
	#  _              _    __        __        _       
	# | |    __ _ ___| |_  \ \      / /__  ___| | __   
	# | |   / _` / __| __|  \ \ /\ / / _ \/ _ \ |/ /   
	# | |__| (_| \__ \ |_    \ V  V /  __/  __/   <    
	# |_____\__,_|___/\__|    \_/\_/ \___|\___|_|\_\   

	start = datetime.strptime(f"{t.year}-{t.weeknum-1}-1", '%G-%V-%u')
	end = start + timedelta(days=6)

	ranges['d_last_week'] = DateRange(start,end)


	#  _              _     __  __             _   _      
	# | |    __ _ ___| |_  |  \/  | ___  _ __ | |_| |__   
	# | |   / _` / __| __| | |\/| |/ _ \| '_ \| __| '_ \  
	# | |__| (_| \__ \ |_  | |  | | (_) | | | | |_| | | | 
	# |_____\__,_|___/\__| |_|  |_|\___/|_| |_|\__|_| |_| 


	s_year, s_month = (t.year-1, 12) if t.month == 1 else (t.year,t.month-1)

	start = datetime.strptime(f"{s_year}-{s_month}-1", '%Y-%m-%d')
	end = datetime.strptime(f"{t.year}-{t.month}-1", '%Y-%m-%d') \
		- timedelta(days=1)

	ranges['d_last_month'] = DateRange(start, end)

	#  _              _    __   __                   
	# | |    __ _ ___| |_  \ \ / /__  __ _ _ __      
	# | |   / _` / __| __|  \ V / _ \/ _` | '__|     
	# | |__| (_| \__ \ |_    | |  __/ (_| | |        
	# |_____\__,_|___/\__|   |_|\___|\__,_|_|        

	start = datetime.strptime(f"{t.year-1}-1-1", '%Y-%m-%d')
	end = datetime.strptime(f"{t.year-1}-12-31", '%Y-%m-%d')

	ranges['d_last_year'] = DateRange(start,end)


	 #  _              _    __  __  ____                   
	 # | |    __ _ ___| |_  \ \/ / |  _ \  __ _ _   _ ___  
	 # | |   / _` / __| __|  \  /  | | | |/ _` | | | / __| 
	 # | |__| (_| \__ \ |_   /  \  | |_| | (_| | |_| \__ \ 
	 # |_____\__,_|___/\__| /_/\_\ |____/ \__,_|\__, |___/ 
	 #                                          |___/      

	def make_x_days_date_range(today, days):
		start = today - timedelta(days=days)
		end = today

		return DateRange(start, end)

	for x in [7, 14, 30, 60, 90]:
		ranges[f"d_last_{x}_days"] = make_x_days_date_range(today, x)

	return ranges

def calculate_singletons():

	today = datetime.today()
	d_now=datetime.strptime(
		f"{today.year}-{today.month}-{today.day}", '%Y-%m-%d')
	d_yesterday = d_now - timedelta(days=1)

	return dict(d_now=d_now, d_yesterday=d_yesterday)
