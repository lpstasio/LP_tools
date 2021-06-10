import re
import glob
import os

nome_programma     = 'PRTEST00'
nome_programmatore = 'DAVIDE'
utensili           = [['2', 'F6', '35'], ['3', 'D40', '40']]
dima               = '6A'
n_robot            = '8'

info_text = '''
;                        __NOMEPR__
;
;  __UTENSILI__   DIMA __DIMA__      ROBOT __NROBOT__    __PROGRAMMATORE__
;
'''[1:]

start_text = '''
;
M2__NMOTORE__ S19000
;
G79 G0 Z0
G90 G0 Y-100
;
(UIO,X,Y,Z)
;
G90 G0 __X__ __Y__ __B__ __A__
;
L365=0
L385=__LUTENSILE__ ; L. ut. Libera
L386=__NMOTORE__ ; Numero Motore
;
(TCP,1)
;
G90 G0 __X__ __Y__
;
'''[1:]

end_text = '''
;
(TCP)
;
(UAO,0)
;
G90 G0 Z0
G90 G0 Y-100
;
A0 B0
;
X0 Y0 Z0
;
M5
;
'''[1:]

def process(name):
	print("opening ", name)
	info_inserted = False
	is_writing = True
	tcp1_found = False
	tcp0_found = False
	g0_found   = False

	current_mot = ''
	current_len = ''

	re_g0_coordinate_x = re.compile('X-?[0-9]+.?[0-9]*')
	re_g0_coordinate_y = re.compile('Y-?[0-9]+.?[0-9]*')
	re_g0_coordinate_z = re.compile('Z-?[0-9]+.?[0-9]*')
	re_g0_coordinate_a = re.compile('A-?[0-9]+.?[0-9]*')
	re_g0_coordinate_b = re.compile('B-?[0-9]+.?[0-9]*')
	re_l385			   = re.compile('=[0-9]+.?[0-9]*')
	re_l386 		   = re.compile('=[0-9]+')

	# Preparazione info
	utensili_text = ''
	for ut in utensili:
		utensili_text += 'M{} {} L{} - '.format(ut[0], ut[1], ut[2])
	utensili_text = utensili_text[:-3]

	with open('in/' + name,'r') as fin:
		should_overwrite = True
		if os.path.exists('out/' + name):
			#choice = input("\nIl file '" + name + "' esiste nella cartella 'out', sovrascrivere? [Sn] ")
			#should_overwrite = choice[0].lower() == 's'
			should_overwrite = True
		if should_overwrite:
			with open('out/' + name, 'w') as fout:
				for line in fin.readlines():
					if not info_inserted:
						if '(TCP)' in line:
							is_writing = False
						if 'DIS' in line:       # Info iniziale
							fout.write(info_text.\
									   replace('__NOMEPR__', nome_programma).\
									   replace('__UTENSILI__', utensili_text).\
									   replace('__DIMA__', dima).\
									   replace('__NROBOT__', n_robot).\
									   replace('__PROGRAMMATORE__', nome_programmatore))
							info_inserted = True
							is_writing = True
							tcp0_found = True
					else:  # info_inserted == True
						if tcp0_found and (not tcp1_found):
							if 'DIS' in line:
								is_writing = True
							else:
								is_writing = False

							if 'L385' in line:
								# TODO: use this for info_text
								current_len = re_l385.findall(line)[0][1:]
							elif 'L386' in line:
								current_mot = re_l386.findall(line)[0][1:]
							elif '(TCP' in line:
								tcp1_found = True
								tcp0_found = False
						elif tcp1_found:  # tcp1_found == True
							if (not g0_found) and ('G0' in line):
								print(line)
								x = re_g0_coordinate_x.findall(line)[0]
								y = re_g0_coordinate_y.findall(line)[0]
								z = re_g0_coordinate_z.findall(line)[0]
								a = re_g0_coordinate_a.findall(line)[0]
								b = re_g0_coordinate_b.findall(line)[0]

								fout.write(start_text.\
											replace('__NMOTORE__',   current_mot).\
											replace('__LUTENSILE__', current_len).\
											replace('__X__', x).\
											replace('__Y__', y).\
											replace('__Z__', z).\
											replace('__A__', a).\
											replace('__B__', b))
								line = ''
								is_writing = True
								tcp1_found = False
						else:   #tcp0_found == False and tcp1_found = False
							if 'FINE PROGRAMMA' in line:
								fout.write(end_text)
								break
							if '(TCP)' in line:
								tcp0_found = True

					if is_writing:	
						fout.write(line)

if __name__ == '__main__':
	paths = glob.glob('in/*.nc')
	if not os.path.exists('out'):
	    os.makedirs('out')

	for path in paths:
		filename = os.path.basename(path)
		if not ('maschera' in filename):
			process(filename)
	
	#input("\n\nPremere invio per chiudere...")

