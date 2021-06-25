import os
from flask import Flask, request,Response,jsonify
from flask_cors import CORS, cross_origin
from werkzeug.utils import secure_filename
import pandas as pd
import pulp as pu

app = Flask(__name__)
CORS(app)
app.config["DEBUG"] = True



def ip_open_vs(vs,capacity,name,available,days):

   
    lp_prob =pu.LpProblem('MinVS', pu.LpMinimize)
    run = True
    totalcap = 0
    result = []
    for i in capacity:
        totalcap+=i

    if (totalcap*days)<available:
        return "Short"

    while run:
        runresult=[]            
        if totalcap >= available:
            run=False
            lp=[]
            for i in vs:
                lp.append(pu.LpVariable(i,cat="Binary"))

            objf = []
            for x,i in enumerate(lp):
                if x < len(lp):
                    objf.append(i)
                    
            lp_prob +=  sum(objf[a]*capacity[a] for a,b in enumerate(objf)) 

            lp_prob += lp_prob.objective >= available

            print(lp_prob)
            status = lp_prob.solve(pu.COIN_CMD(path="bin/cbc.exe",msg=1, options=['dualSimplex']))
            print(pu.LpStatus[status])
            for ind,i in enumerate(objf):
                if(pu.value(i))==1:
                    runresult.append([vs[ind],str(capacity[ind])])
            result.append(runresult)
            
        else:
            for i,val in enumerate(vs):
                runresult.append([vs[i],str(capacity[i])])
            result.append(runresult)
            available-=totalcap
        print(totalcap)
    return result


@app.route('/openvs', methods=['POST'])
def open_vs():
    if request.method == "POST":
        
        f = request.files['file']
        name = request.form.get('vaccinename')
        available = request.form.get('vaccineavailable')
        #print(available)
        days = request.form.get('vaccinedays')
        if os.path.exists(f.filename):
            os.remove(f.filename)
        else:
            print("Can not delete the file as it doesn't exists")
        f.save(secure_filename(f.filename))
        df =pd.read_excel(f.filename, engine='openpyxl')
        print(df.empty)
        if set(['Vaccine Station','Capacity']).issubset(df.columns):
            df = df.drop(columns=[col for col in df if col not in ['Vaccine Station','Capacity']])
            if len(df.index)==0:
                return "Blank Data"
            else:
                a = df['Vaccine Station']
                b = df['Capacity']
                result = ip_open_vs(a,b,name,int(available),int(days))
                arr =[] 
                for i,val in enumerate(a):
                    arr.append([a[i],str(b[i])])
                finalresult = {'table':arr,'open':result}
                return jsonify(finalresult)               
        else:
            return "Invalid Data"
        return f.name

app.run()
