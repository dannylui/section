import pandas as pd

class Shear_Check:
    
    def __init__(self, Geom_Input):
        
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
        self.fyw = Geom_Input['fyw']
        self.Es = Geom_Input['E']

        self.output_list = []

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
        

