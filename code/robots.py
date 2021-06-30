import re
import glob
import os

# CHANGELOG
#   v2: '(UIO,X,Y,Z)' era precedente inserito ad ogni cambio di utensile, invece che solo in quello iniziale
#       Aggiunto supporto per '(TCP)' e '(TCP,1)' senza cambio utensile

def process_r2_r9(name, is_r9):
	lines_from_tcp0 = -1
	hold_buffer = ''
	h0_inserted = False

	with open('in/' + name,'r') as fin:
		should_overwrite = True
		if os.path.exists('out/' + name):
			choice = input("\nIl file '" + name + "' esiste nella cartella 'out', sovrascrivere? [Sn] ")
			should_overwrite = choice[0].lower() == 's'
		if should_overwrite:
			with open('out/' + name, 'w') as fout:
				for line in fin.readlines():
					if lines_from_tcp0 < 0:
						if h0_inserted and is_r9 and ('X0' in line):
							line = line.replace('X0', 'X2550')
						fout.write(line)
						if 'L386' in line:
							fout.write('M141\n')
						elif '(TCP)' in line:
							lines_from_tcp0 = 1
					elif lines_from_tcp0 == 1:
						hold_buffer += line
						lines_from_tcp0 = 2
					elif lines_from_tcp0 == 2:
						if '(UAO,0)' in line:
							hold_buffer += 'h0\n;\n'
							h0_inserted = True
						line = hold_buffer + line
						hold_buffer = ''
						lines_from_tcp0 = -1
						fout.write(line)


if __name__ == '__main__':
	paths = glob.glob('in/*.nc')
	if not os.path.exists('out'):
	    os.makedirs('out')

	print("PREPARAZIONE TAGLIO R9 (v1)\n\n")
	for path in paths:
		filename = os.path.basename(path)
		if 'r2' in filename.lower():
			process_r2_r9(filename, False)
		elif 'r9' in filename.lower():
			process_r2_r9(filename, True)
	
	input("\n\nPremere invio per chiudere...")

