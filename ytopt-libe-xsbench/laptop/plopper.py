import os
import sys
import subprocess
import random
import psutil

#import multiprocessing
#multiprocessing.set_start_method('fork', force=True)

class Plopper:
    def __init__(self,sourcefile,outputdir):

        # Initilizing global variables
        self.sourcefile = sourcefile
        self.outputdir = outputdir+"/tmp_files"

        if not os.path.exists(self.outputdir):
            os.makedirs(self.outputdir)


    #Creating a dictionary using parameter label and value
    def createDict(self, x, params):
        dictVal = {}
        for p, v in zip(params, x):
            dictVal[p] = v
        return(dictVal)

    #Replace the Markers in the source file with the corresponding Pragma values
    def plotValues(self, dictVal, inputfile, outputfile):
        with open(inputfile, "r") as f1:
            buf = f1.readlines()

        with open(outputfile, "w") as f2:
            for line in buf:
                modify_line = line
                for key, value in dictVal.items():
                    if key in modify_line:
                        if value != 'None': #For empty string options
                            if  len(dictVal) > 10: #for more than 10 parameters
                                modify_line = modify_line.replace('#'+key+' ', str(value))
                            else:
                                modify_line = modify_line.replace('#'+key, str(value))

                if modify_line != line:
                    f2.write(modify_line)
                else:
                    #To avoid writing the Marker
                    f2.write(line)


    # Function to find the execution time of the interim file, and return the execution time as cost to the search module
    def findRuntime(self, x, params, worker):
        interimfile = ""
        #exetime = float('inf')
        #exetime = sys.maxsize
        exetime = 1
        counter = random.randint(1, 10001) # To reduce collision increasing the sampling intervals

        interimfile = self.outputdir+"/"+str(counter)+".c"


        # Generate intermediate file
        dictVal = self.createDict(x, params)
        self.plotValues(dictVal, self.sourcefile, interimfile)

        #compile and find the execution time
        tmpbinary = interimfile[:-2] + '_w' + str(worker)

        kernel_idx = self.sourcefile.rfind('/')
        kernel_dir = self.sourcefile[:kernel_idx]

        #cmd1 = "mpicc -std=gnu99 -Wall -fopenmp -DOPENMP -DMPI -O3 "  + \
        #cmd1 = "gcc-12 -std=gnu99 -Wall -fopenmp -DOPENMP -O3 "  + \
        cmd1 = "mpicc -std=gnu99 -Wall -DMPI -O3 "  + \
                " -o " + tmpbinary + " " + interimfile +" " + kernel_dir + "/Materials.c " \
                + kernel_dir + "/XSutils.c " + " -I" + kernel_dir + \
                " -lm "

        cmd2 = kernel_dir + "/exe.pl " +  tmpbinary

        #Find the compilation status using subprocess
        compilation_status = subprocess.run(cmd1, shell=True, stderr=subprocess.PIPE)

        #Find the execution time only when the compilation return code is zero, else return infinity
        if compilation_status.returncode == 0 :
        #and len(compilation_status.stderr) == 0: #Second condition is to check for warnings
           # execution_status = subprocess.run(cmd2, shell=True, stdout=subprocess.PIPE)
           execution_status = subprocess.Popen(cmd2, shell=True, stdout=subprocess.PIPE)
           app_timeout = 60

           try:
                outs, errs = execution_status.communicate(timeout=app_timeout)
           except subprocess.TimeoutExpired:
                execution_status.kill()
                for proc in psutil.process_iter(attrs=['pid', 'name']):
                    if 'exe.pl' in proc.info['name']:
                        proc.kill()
                outs, errs = execution_status.communicate()
                return app_timeout

           exetime = float(outs.strip())
           #exetime = float(execution_status.stdout.decode('utf-8'))

           #if exetime == 0:
               #exetime = -1

        else:
            print(compilation_status.stderr)
            print("compile failed")
        return exetime #return execution time as cost
