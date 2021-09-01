import re
import glob
import os

VERSION_NUMBER = 3

def process(name, start, end, type):
	pause = False
	has_started = False
	has_ended = False
	once = False

	skip_z_guard = False
	is_15mm = (('15mm' in name) or ('15 mm' in name)) and (type == 'NUMERI')
	z_expr = re.compile('[zZ][-]*[0-9]*\.?[0-9]*')
	z_list = dict()
	with open('in/' + name,'r') as fin:
		should_overwrite = True
		if os.path.exists('out/' + name):
			choice = input("\nIl file '" + name + "' esiste nella cartella 'out', sovrascrivere? [Sn] ")
			should_overwrite = ((choice) and (choice[0].lower() == 's'))
		if should_overwrite:
			with open('out/' + name, 'w') as fout:
				for line in fin.readlines():
					skip_z_guard = False
					if not has_ended:
						if not pause:
							if (not has_started) and ('N2;OPERAZIONE' in line):
								pause = True
								line = start
								skip_z_guard = True
							else:
								if has_started:
									if not once:
										line = line.replace('B180.000A0.000','F15000')
										once = True
									elif '(DIS,"FINE PROGRAMMA")' in line:
										line = end
										has_ended = True
										skip_z_guard = True
								line = line.replace('Z25','Z40F15000').replace('F2000','F3500')
							if is_15mm:
								line = line.replace('Z-5', 'Z-15')
							fout.write(line)
							
							# Z guards
							if not skip_z_guard:
								for match in z_expr.findall(line):
									if match in z_list.keys():
										z_list[match] += 1
									else:
										z_list[match] = 1
						elif '(TCP,1)' in line:
							pause = False
							has_started = True
	
			if is_15mm:
				print('\n' + name + '  (' + type + ' 15mm): ')
			else:
				print('\n' + name + '  (' + type + '): ')
			max_len = 0
			for zstr in z_list.keys():
				if len(zstr) > max_len:
					max_len = len(zstr)
			for zstr in z_list.keys():
				spacing = ' '*(max_len - len(zstr))
				print(zstr + spacing, '->', z_list[zstr])

base_start = '''(DAN)
G16XY
VEF=0.4
MDA=40
M6T5
(CLS,CU)
(UAO,1);======
(UIO,Z22.5)
h5
G00C0A-0.0
M03S15000F3500
(RPT,3)
'''

base_end = '''(UIO,Z-8.7)
(ERP)
(UAO,0)
G00
G00X0Y0
M30
;
'''


numeri_start = '''(DAN)
G16XY
VEF=0.4
MDA=40
M6T5
(CLS,CU)
(UTO,1,X0,Y0,Z25)
h4;<<<<<<<<<<<<<<<<<<<<<<<<<<
G00C0A-0.0
M03S15500F3500
'''


numeri_end = '''(UTO,10,X0,Y0,Z0)
G00
G00X0Y0
M30
;
'''

if __name__ == '__main__':
	paths = glob.glob('in/*.nc')
	if not os.path.exists('out'):
	    os.makedirs('out')

	print("PREPARAZIONE TAGLIO MASCHERE (v{})".format(VERSION_NUMBER))
	for path in paths:
		filename = os.path.basename(path)
		if 'maschera' in filename.lower():
			if 'numeri' in filename.lower():
				process(filename, numeri_start, numeri_end, 'NUMERI')
			else:
				process(filename, base_start, base_end, 'BASE')
	
	input("\n\nPremere invio per chiudere...")

