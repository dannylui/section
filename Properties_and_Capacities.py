import pandas as pd
import math

class Section_Properties:
    
    def __init__(self, Geom_Input):
        
        # Slab
        self.tslab = Geom_Input['t_slab']
        self.bslab = Geom_Input['b_slab']
        self.thaunch = Geom_Input['t_haunch']
        
        # Top flange
        self.t_tf = Geom_Input['t_tf']
        self.b_tf = Geom_Input['b_tf']
        
        # Web
        self.t_web = Geom_Input['t_web']
        self.D_web = Geom_Input['D_web']

        # Bottom Flange
        self.t_bf = Geom_Input['t_bf']
        self.b_bf = Geom_Input['b_bf']

        #Long Stiffener
        self.has_long_stiff = Geom_Input['Long stiffener']

        #Transverse Stiffener
        self.has_trans_stiff = Geom_Input['Trans stiffener']

        #Material Properties
        self.fytf = Geom_Input['fy_tf']
        self.fyw = Geom_Input['fyw']
        self.fybf = Geom_Input['fy_bf']
        self.Es = Geom_Input['E']
        self.Fc = Geom_Input['fc']

        self.output_list = []


    def Calc_Elastic_Prop(self, n: int = 8):

        # use n = 0 when doing section prop for negative flexure

        Section = pd.DataFrame({'Element':["Slab","Top Flange","Web","Bottom Flange"],
                        'Width': [          self.bslab, self.b_tf,  self.t_web, self.b_bf],
                        'Thickness/Height':[self.tslab , self.t_tf, self.D_web, self.t_bf]})

        y = []
        mod_ratio_n = []

        if n == 0:
            Section = Section.drop([0]).reset_index(drop=True)
            # print(Section["Width"] )
                        

        # Calculates y 
        for i in range(0,len(Section['Width'])):
            if i == 0:
                y.append(Section.loc[i,"Thickness/Height"]/2)
                if n == 0:
                    mod_ratio_n.append(1)
                else:
                    mod_ratio_n.append(n)
                
            else:
                y.append(Section.loc[i,"Thickness/Height"]/2 + y[i-1] + Section.loc[i-1,"Thickness/Height"]/2)
                mod_ratio_n.append(1)


        Section["Area"] = Section["Width"] * Section ["Thickness/Height"] / mod_ratio_n

        Section["Y"] = y
        Section["AY"] = Section["Area"] * Section ["Y"] 

        # print(Section["Area"])
        # print(Section["Width"] * Section ["Thickness/Height"])

        Total = Section.sum()
        Centroid = Total['AY'] / Total['Area']

        Section["D"] = Section["Y"] - Centroid
        Section["AD^2"] = Section["Area"] * Section["D"]**2

        Section["I0"] = Section['Width'] * Section["Thickness/Height"]**3 / 12 / mod_ratio_n
        Total = Section.sum()

        Inertia =  Total["AD^2"] + Total["I0"]

        BM_height = Total["Thickness/Height"]

        if Section.loc[0,"Element"] == 'Slab':
            BM_height -= Section.loc[0,'Thickness/Height']
        
        Y_BOT = Total["Thickness/Height"] - Centroid
        Y_TOP = BM_height - Y_BOT
        
        S_TOP = Inertia / Y_TOP
        S_BOT = Inertia / Y_BOT

        Modulus = pd.DataFrame({'Location':["Top","Bottom"],'Distance y':[Y_TOP,Y_BOT],'Section Modulus':[S_TOP,S_BOT ]})

        # print(Total)

        # print(Section)
        # print(Modulus)
        # print(Inertia)

        self.output_list.extend([Section, f"Total I = {Inertia}", Modulus])
        
        return Section, Modulus, Inertia

    #AASHTO 6.10.2.1
    def chk_web_proportion(self):
        self.output_list.append("Checking Web proportions per AASHTO 6.10.2.1")
        if self.has_long_stiff == 'no':
            self.output_list.append(f"{self.D_web} / {self.t_web} = {self.D_web / self.t_web} <= 150")
            return self.D_web / self.t_web <= 150
        else:
            self.output_list.append(f"{self.D_web} / {self.t_web} = {self.D_web / self.t_web}<= 300")
            return self.D_web / self.t_web <= 300

    #Calculating Vp
    def Calc_Plastic_Shear_Vp(self):
        self.output_list.extend(["Calculating Vp", 0.58 * self.fyw  * self.D_web * self.t_web])
        return 0.58 * self.fyw  * self.D_web * self.t_web
    
    # returns true if stiffened, false if not. Assume no longitudinal stiffener
    def is_stiffened(self, Stiff_input: dict):

        self.output_list.append("Check if the section is stiffened")
        
        if Stiff_input['Panel'] == 'Interior' and Stiff_input['Spacing d0'] <= self.D_web * 3:

            self.output_list.append("Section is stiffened, check capacity using 6.10.9.3")
            
            print ("Check stiffened capacity using 6.10.9.3")
            return True
        
        elif Stiff_input['Panel'] == 'End' and Stiff_input['Spacing d0'] <= self.D_web * 1.5:
            
            self.output_list.append("Section is stiffened, check capacity using 6.10.9.3.3")

            print ("Check stiffened capacity using 6.10.9.3.3")
            
            return True
        else:
            
            self.output_list.append("Section is unstiffened, check capacity using 6.10.9.2")
            
            print ("Check unstiffened capacity using 6.10.9.2")
            return False

    def Calc_Shear_buckling_k (self, Stiff_input):
        self.output_list.append("Calculating Shear Buckling, k")
        if not self.is_stiffened(Stiff_input):
            print("k value per AASHTO 6.10.9.2")
            self.output_list.append("Per AASHTO 6.10.9.2, k = 5")
            return 5
        else:
            print("Calculate k per AASHTO 6.10.9.3.2-7")
            self.output_list.append(f"Per AASHTO 6.10.9.3.2-7, k = 5 + 5 / ({Stiff_input['Spacing d0']} / {self.D_web}) ^ 2 = {5 + 5 / (Stiff_input['Spacing d0'] / self.D_web) ** 2}")
            return 5 + 5 / (Stiff_input['Spacing d0'] / self.D_web) ** 2
        
    # Calculate Shear-buckling resistance to the shear yield Strength
    #AASHTO 6.10.9.3.2
    def Calc_ratio_C(self, Stiff_input):

        k = self.Calc_Shear_buckling_k(Stiff_input)

        print("k=" + str(k))

        if self.D_web / self.t_web <= 1.12 * (self.Es * k / self.fyw) ** 0.5:
            self.output_list.append("Per AASHTO 6.10.9.3.2-4, C = 1")
            print("Calculate C per AASHTO 6.10.9.3.2-4")
            return 1
        elif self.D_web / self.t_web < 1.4* (self.Es * k / self.fyw) ** 0.5:
            self.output_list.append(f"Calculate C per AASHTO 6.10.9.3.2-5, C = {1.12 / (self.D_web / self.t_web) * (self.Es * k / self.fyw) ** 0.5}")
            print("Calculate C per AASHTO 6.10.9.3.2-5")
            return 1.12 / (self.D_web / self.t_web) * (self.Es * k / self.fyw) ** 0.5
        else:
            self.output_list.append(f"Calculate C per AASHTO 6.10.9.3.2-6, C = {1.57 / ((self.D_web / self.t_web) ** 2) * (self.Es * k / self.fyw)}")
            print("Calculate C per AASHTO 6.10.9.3.2-6")
            return 1.57 / ((self.D_web / self.t_web) ** 2) * (self.Es * k / self.fyw)
        

    def Calc_nominal_shear_Vn (self, Stiff_input):

        d0 = Stiff_input['Spacing d0']

        C = self.Calc_ratio_C(Stiff_input)

        print("C=" + str(C))

        self.output_list.append("Calculating Nominal Shear Vn")

        if Stiff_input['Panel'] == 'Interior':
            if (2 * self.D_web * self.t_web)/(self.b_tf * self.t_tf + self.b_bf * self.t_bf) <= 2.5:             #AASHTO 6.10.9.3.2-1
                print("Calculate Vn per AASHTO 6.10.9.3.2-1")
                self.output_list.extend(["Calculate Vn per AASHTO 6.10.9.3.2-1",
                                         self.Calc_Plastic_Shear_Vp() * (C + 0.87 * (1-C)/(1+(d0 / self.D_web)**2)**0.5)])
                return self.Calc_Plastic_Shear_Vp() * (C + 0.87 * (1-C)/(1+(d0 / self.D_web)**2)**0.5)
            else:  #AASHTO 6.10.9.3.2-8
                print("Calculate Vn per AASHTO AASHTO 6.10.9.3.2-8")
                self.output_list.extend(["Calculate Vn per AASHTO AASHTO 6.10.9.3.2-8",
                                         self.Calc_Plastic_Shear_Vp() * (C + 0.87 * (1-C)/((1+(d0 / self.D_web)**2)**0.5 + (d0 / self.D_web)))])
                return self.Calc_Plastic_Shear_Vp() * (C + 0.87 * (1-C)/((1+(d0 / self.D_web)**2)**0.5 + (d0 / self.D_web)))
        else: 
            return self.Calc_Plastic_Shear_Vp() * C
        

    # Calculating the plastic neutral axis for positive flexure
    # Ref AASHTO Table D6.1-1
    # conservative ignore rebars for now - to be implemented later *****
    def calc_PNA (self):
        
        self.output_list.append("Calculating PNA (AASHTO Table D6.1-1)")

        Ps = 0.85 * self.Fc * self.bslab * self.tslab        # Slab
        Pt = self.fybf * self.b_bf * self.t_bf              # Bottom Flange/ tension
        Pc = self.fytf * self.b_tf * self.t_tf              # Top Flange/ compression
        Pw = self.fyw * self.D_web * self.t_web             # Web

        Y_bar = 0
        Mp = 0
        PNA_Loc = ''

        if Pt + Pw >= Pc + Ps:      # in web
            print("PNA is in the web")

            self.output_list.append("PNA is in the web")

            PNA_Loc = 'Web'
            Y_bar = self.D_web / 2 * ((Pt-Pc-Ps)/Pw+1)                   # PNA from the top of the web
        
            ds = Y_bar + self.t_tf + self.thaunch + self.tslab / 2         # Distance from PNA to center of the slab 
            dc = Y_bar + self.t_tf / 2                 # Distance from PNA to center of the compression flange
            dt = self.D_web - Y_bar + self.t_bf / 2         # Distance from PNA to center of the compression flange

            Mp = Pw/(2 * self.D_web) * (Y_bar**2 + (self.D_web-Y_bar)**2) + (Ps*ds + Pc*dc + Pt * dt)
            
            print("ds = " + str(ds))
            print("dw = " + str(dw))
            print("dt = " + str(dt))
            
            print("Ybar = " + str(Y_bar))
            print("Mp = " + str(Mp))

            self.output_list.append(f"Y bar = {Y_bar}")

        elif Pt + Pw + Pc >= Ps:    # in the top flange
            print("PNA is in the top flange")

            self.output_list.append("PNA is in the top flange")
            
            PNA_Loc = 'Top Flange'
            Y_bar = self.t_tf/2 * ((Pw + Pt - Ps)/Pc + 1)  

            ds = Y_bar + self.thaunch + self.tslab / 2         # Distance from PNA to center of the slab 
            dw = self.t_tf - Y_bar + self.D_web / 2           # Distance from PNA to center of the web 
            dt = self.t_tf- Y_bar + self.D_web + self.t_bf / 2         # Distance from PNA to center of the compression flange
            
            Mp = Pc/(2 * self.t_tf) * (Y_bar**2 + (self.t_tf-Y_bar)**2) + (Ps*ds + Pw*dw + Pt * dt)
            
            print("ds = " + str(ds))
            print("dw = " + str(dw))
            print("dt = " + str(dt))

            print("Ybar = " + str(Y_bar))
            print("Mp = " + str(Mp))

            self.output_list.append(f"Y bar = {Y_bar}")

        else:
            print("PNA is in the deck")

            self.output_list.append("PNA is in the deck")

            PNA_Loc = 'Slab'

            Y_bar = self.tslab  * (Pw + Pt + Pc)/Ps

            dc = self.tslab - Y_bar + self.thaunch + self.t_tf / 2                 # Distance from PNA to center of the compression flange
            dw = self.tslab - Y_bar + self.thaunch + self.t_tf + self.D_web / 2           # Distance from PNA to center of the web 
            dt = self.tslab - Y_bar + self.thaunch + self.t_tf + self.D_web + self.t_bf / 2         # Distance from PNA to center of the compression flange
            Mp = (Y_bar**2 * Ps)/ (2 * self.tslab) + (Pc*dc + Pw*dw + Pt * dt)
            
            print("ds = " + str(ds))
            print("dw = " + str(dw))
            print("dt = " + str(dt))

            print("Ybar = " + str(Y_bar))
            print("Mp = " + str(Mp))

            self.output_list.append(f"Y bar = {Y_bar}")

        return Y_bar, Mp, PNA_Loc
    
    # AASHTO 6.10.6.2.2
    #***************** Revise to return True/False
    def check_compactness(self):
        
        self.output_list.append("Check Compactness per AASHTO 6.10.6.2.2")

        if self.fytf <= 70 and self.fybf <= 70:
            print ("Flange strength is ok")
        else:
            print ("Flange strength is NG")

        if self.chk_web_proportion():
            print('Web check per 6.10.2.1 is OK')
        else:
            print('Web check per 6.10.2.1 is NG')
        
        Y_bar, _ , PNA_loc = self.calc_PNA()
        Dcp = 0
        
        if PNA_loc == "Web":
            Dcp = Y_bar

        if 2 * Dcp/self.t_web <= 3.76 * (self.Es / self.fytf)**0.5:
            print('Web slenderness check is OK')
        else:
            print('Web slenderness check is NG')
        return  None
    
    def yield_moment_My (self, Forces_input, n, eta):

        self.output_list.append("Calculate Yield Moment")

        _,S_NC,_ = self.Calc_Elastic_Prop(0)
        _,S_LT,_ = self.Calc_Elastic_Prop(3*n)
        _,S_ST,_ = self.Calc_Elastic_Prop(n)

    # Bottom Flange    
        S_NC_bf = S_NC['Section Modulus'][1]
        S_LT_bf = S_LT['Section Modulus'][1]
        S_ST_bf = S_ST['Section Modulus'][1]

        MAD_bf = (self.fybf / eta - 1.25 * Forces_input['M_dc1']/S_NC_bf - (1.25 * Forces_input['M_dc2'] + 1.5 * Forces_input['M_dw']) / S_LT_bf) * S_ST_bf

        My_bf = 1.25 * Forces_input['M_dc1'] + 1.25 * Forces_input['M_dc2'] + 1.5 * Forces_input['M_dw'] + MAD_bf

    # Top Flange
        S_NC_tf = S_NC['Section Modulus'][0]
        S_LT_tf = S_LT['Section Modulus'][0]
        S_ST_tf = S_ST['Section Modulus'][0]

        MAD_tf = (self.fytf / eta - 1.25 * Forces_input['M_dc1']/S_NC_tf - (1.25 * Forces_input['M_dc2'] + 1.5 * Forces_input['M_dw']) / S_LT_tf) * S_ST_tf

        My_tf = 1.25 * Forces_input['M_dc1'] + 1.25 * Forces_input['M_dc2'] + 1.5 * Forces_input['M_dw'] + MAD_tf

        self.output_list.append(f"Yield Moment ={min(My_tf, My_bf)}")
        return min(My_tf, My_bf)
    

    # Total depth of composite section

    def calc_total_depth_Dt(self):

        return self.tslab + self.t_tf + self.D_web + self.t_bf

    # Depth to PNA from top of deck
    def calc_Dp (self):

        Y_bar,_,PNA_loc = self.calc_PNA()

        Dp = Y_bar

        if PNA_loc == 'Top Flange':
            Dp += self.tslab
        elif PNA_loc == 'Web':
            Dp += self.tslab + self.t_tf

        return Dp

    # AASHTO 6.10.7.3
    def check_ductility(self):
        self.output_list.append("Check ductility per AASHTO 6.10.7.3")
        
        return self.calc_Dp() <= 0.42 * self.calc_total_depth_Dt()
    
    # AASHTO 6.10.7.1.2
    def Calc_nominal_flex_Mn(self, span='simp'): #Simple vs cont

        self.output_list.append("Calculate nominal flexural capacity Mn (AASHTO 6.10.7.1.2)")

        _, Mp, _ = self.calc_PNA()

        Mn = 0

        if self.check_compactness():
            if self.calc_Dp() <= 0.1 * self.calc_total_depth_Dt():
                Mn =  Mp
            else:
                Mn = Mp * (1.07 - 0.7 * self.calc_Dp() / self.calc_total_depth_Dt())
            
            if span == "cont":
                Mn = min(Mn, 1.3 * self.calc_hyb_factor_Rh() * self.yield_moment_My())

        else:
            print('write for non-compact sections')

        return Mn
    
    def calc_hyb_factor_Rh(self):
        if self.fyw >= max(self.fybf, self.fytf):
            return 1
        else:
            #Provide calculations for this
            return 0

    
    #AASHTO 6.10.8.2.3
     
    def calc_Lp(self):

        return 1.0 * self.calc_rt_for_LTB() * math.sqrt(self.Es/self.fytf)


    def calc_rt_for_LTB(self):
        # effective radius of gyration for lateral–torsional buckling (in.)

        return self.b_tf / math.sqrt(12 * (1+ 1/3 * (self.calc_Dc() * self.t_web) / (self.b_tf * self.t_tf)))
    
    def calc_Dc(self):
        # depth of the web in compression in the elastic range (in.). 
        # For composite sections, Dc shall be determined as specified in Article D6.3.1.
        
        # Provide Calcs
        return 36.96

