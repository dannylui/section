# import pandas as pd
from Properties_and_Capacities import Section_Properties as pac

# Section = pd.DataFrame({'Element':["Slab","Top Flange","Web","Bottom Flange"],
#                        'Width': [1, 2, 3, 4],
#                        'Thickness/Height':[5,6, 7, 8]})

# section2 = pd.DataFrame({'s':["Slab","Top Flange","Web"],
#                        'dsfd': [1, 2, 3],
#                        'sdfds/Height':[5,6, 7]})


# listcomb = [Section, section2]

# print(listcomb[0])


# AASHTO 6.5.4.2
Resist_factors_phi = {'phi_v':1.0,    # Shear
                      'phi_f':1.0 }   # Flexure

Stiffener_Input = {'Panel':'Interior',      # End/ Interior only
                   'Spacing d0': 200}       # Spacing in inches
  

# Input materials and geometry
Input = {'fyw':50, 'fy_tf':50, 'fy_bf':50, 'E':29000,
         'fc':4,
         'Long stiffener':'no', 'Trans stiffener': 'yes',      # Should be yes/no only 
         'b_slab':114, 't_slab':9, 't_haunch':3.5, 
         'b_tf':16, 't_tf':1.0, 
         'D_web':69, 't_web':0.5, 
         'b_bf':18, 't_bf':1.75}

# Forces at section from analysis
Forces = {'M_dc1': 2202*12, 'M_dc2': 335*12,'M_dw': 322*12,'M_LL': 12222}

modular_ratio_n = 8       # modular ratio, Es/Ec

Import_factor = 1     # importance factor, essential, etc

newSect = pac(Input)
newSect.Calc_Elastic_Prop(0)
newSect.Calc_Elastic_Prop(24)
newSect.Calc_Elastic_Prop(8)

newSect.calc_PNA()
newSect.yield_moment_My(Forces, 8, Import_factor)
# newSect.chk_web_proportion()
# newSect.Calc_Shear_buckling_k(Stiffener_Input)
for i in newSect.output_list:
    print("====")
    print(i)
