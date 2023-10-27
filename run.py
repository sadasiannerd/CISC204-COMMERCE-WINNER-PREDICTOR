
import sys

from bauhaus import Encoding, proposition, constraint, Or, And
from bauhaus.utils import count_solutions, likelihood

# These two lines make sure a faster SAT solver is used.
from nnf import config, Var
config.sat_backend = "kissat"

PRODUCT_NAME = sys.argv[1]

# Encoding that will store all of your constraints
E = Encoding()

class Hashable:
    def __hash__(self):
        return hash(str(self))

    def __eq__(self, __value: object) -> bool:
        return hash(self) == hash(__value)

    def __repr__(self):
        return str(self)

# To create propositions, create classes for them first, annotated with "@proposition" and the Encoding
@proposition(E)      
class MarketableLevel(Hashable):
    def __init__(self,p_name: str, lvl:int):
        self.p_name = p_name
        self.lvl = lvl
    def __str__(self):
        return f"product {self.p_name} has a marketable level of {self.lvl}" 

@proposition(E)
class InnovationLevel(Hashable):
    def __init__(self,p_name: str, lvl:int):
        self.p_name = p_name
        self.lvl = lvl
    def __str__(self):
        return f"product {self.p_name} has a marketable level of {self.lvl}" 
    
@proposition(E)
class ProfitabilityLevel(Hashable):
    def __init__(self,p_name: str, lvl:int):
        self.p_name = p_name
        self.lvl = lvl
    def __str__(self):
        return f"product {self.p_name} has a profitable level of {self.lvl}" 

E.add_constraint(ProfitabilityLevel(PRODUCT_NAME, 1)&MarketableLevel(PRODUCT_NAME, 2)
                 |ProfitabilityLevel(PRODUCT_NAME,2)&InnovationLevel(PRODUCT_NAME,2)
                 |InnovationLevel(PRODUCT_NAME, 1)&MarketableLevel(PRODUCT_NAME,2)
                 |InnovationLevel(PRODUCT_NAME, 2)&MarketableLevel(PRODUCT_NAME,1)&ProfitabilityLevel(PRODUCT_NAME, 1)
                 |ProfitabilityLevel(PRODUCT_NAME, 2)&MarketableLevel(PRODUCT_NAME, 1))

@proposition(E)
class Property(Hashable):
    def __init__(self,p_name:str, property: str):
        self.p_name = p_name
        self.property = property
    def __str__(self):
        return f"{self.p_name} is {self.property}"
    
@proposition(E)
class Market(Hashable):
    def __init__(self,p_name: str, market: str):
        self.p_name = p_name
        self.market = market
    def __str__(self):
        return f"{self.p_name} is in market {self.market}"


#Market types
pure_competition = Market(PRODUCT_NAME,"Pure Competition")
monopolistic = Market(PRODUCT_NAME,"Monopolistic Competition")
monopoly = Market(PRODUCT_NAME, "Monopoly")
oligopoly = Market(PRODUCT_NAME, "Oligopoly")

#Other propositions
seasonal_demand = Property(PRODUCT_NAME,"in seasonal demand")
competitive_price = Property(PRODUCT_NAME, "competitive price")
unique_product = Property(PRODUCT_NAME, "a unique product")
unique_market = Property(PRODUCT_NAME, "a product in a unique market")
credible = Property(PRODUCT_NAME, "credible")
low_cost = Property(PRODUCT_NAME, "low-cost")


#TODO: manually enter other propositions
def productProps():
    #NOTE:this block of code is for testing
    #assume product is in seasonal_demand, and is a unique product what else does the product need in order to be winnable
    E.add_constraint(seasonal_demand&unique_product)
    
    #given that product is in pure_competition market:
    E.add_constraint(pure_competition)
    #***
    

def positive_constraints():
    #a unique level of 2 means the product has a unique nature and is in a unique market, if it's only true for one of the two then product only has marketable level of 1 (this happens only if the product is in markets/ conditions that allows it to be marketable)
    E.add_constraint(~unique_market|~unique_product|MarketableLevel(PRODUCT_NAME, 2))
    E.add_constraint((~unique_market|pure_competition|seasonal_demand|competitive_price|MarketableLevel(PRODUCT_NAME, 1))&(~unique_market|~monopolistic|InnovationLevel(PRODUCT_NAME, 1)))
    E.add_constraint(~unique_product|pure_competition|seasonal_demand|competitive_price|MarketableLevel(PRODUCT_NAME, 1))
    #Seasonal demand implies product is set to be of MarketableLevel 1
    E.add_constraint(~seasonal_demand|MarketableLevel(PRODUCT_NAME,1))
    
    #an InnovationLevel of 2 means the product is credible and has InnovationLevel of 1 and is in the market where an InnovationLevel of 2 exists
    E.add_constraint(monopolistic|~InnovationLevel(PRODUCT_NAME, 1)|~credible|oligopoly|InnovationLevel(PRODUCT_NAME, 2))

    #Profitability level 2 if the product is low-cost and is unique in the market and is credible and is in the markets/conditions that allows it to have the profitability level of 2
    E.add_constraint(~low_cost|~unique_market|competitive_price|seasonal_demand|monopoly|ProfitabilityLevel(PRODUCT_NAME, 2))
    E.add_constraint(~low_cost|ProfitabilityLevel(PRODUCT_NAME, 1))
    
    
    

def negative_constraints():

    #competitive price means low revenue means low profit margin means profitable level cannot be 2
    E.add_constraint(~competitive_price|~ProfitabilityLevel(PRODUCT_NAME, 2))

def env_constraints():
    #A product can only be in one of the four market types:
    E.add_constraint((~pure_competition | ~monopolistic)&(~pure_competition | ~monopoly) & (~pure_competition | ~oligopoly)) 
    E.add_constraint((~monopolistic |  ~pure_competition) & (~monopolistic | ~monopoly) & (~monopolistic | ~oligopoly))
    E.add_constraint((~monopoly | ~monopolistic) & (~monopoly | ~pure_competition) & (~monopoly |~oligopoly))
    E.add_constraint((~oligopoly | ~monopolistic) & (~oligopoly |~monopoly) & (~oligopoly|~pure_competition))

    #Pure competition implies product is not able to have a competitive price and competitive marketing (Marketable)
    #In this case means not Marketable_Level_2
    
    E.add_constraint((~pure_competition|~ProfitabilityLevel(PRODUCT_NAME,2))&(~pure_competition|~MarketableLevel(PRODUCT_NAME,2)))

    #Monopolistic competition is a market involves of innovators, when everyone tries to be different no one is different

    E.add_constraint((~monopolistic|~InnovationLevel(PRODUCT_NAME, 1))&(~monopolistic|~InnovationLevel(PRODUCT_NAME, 2)))

    #Monopoly implies that the market is unique, but price is regulated, so profitable level cannot be 2 and competitive price is set to true
    
    E.add_constraint(~monopoly|unique_market|~ProfitabilityLevel(PRODUCT_NAME, 2)|competitive_price)

    #Oligopoly implies that the market is small but also involves with innovators, everyone is given with innovation level of 1 but cannot reach to 2
    E.add_constraint((~oligopoly|InnovationLevel(PRODUCT_NAME, 1))&(~oligopoly|~InnovationLevel(PRODUCT_NAME, 2)))

def build_theory():

    positive_constraints()

    negative_constraints()

    env_constraints()


    return E

if __name__ == "__main__":

    print("Building constraints...")
    T = build_theory()
    print("Successfully built constraints! Compiling theory ...")
    # Don't compile until you're finished adding all your constraints!
    T = T.compile()
    print("Theory is compiled!")
    # After compilation (and only after), you can check some of the properties
    # of your model:
    print("\nSatisfiable: %s" % T.satisfiable())
    print("# Solutions: %d" % count_solutions(T))
    print("   Solution: %s" % T.solve())

    # print("    Solution:")
    # sol = T.solve()

    #TODO:print result

    # print("\nVariable likelihoods:")
    # for v,vn in zip([e1,e2,e3], ["e1", "e2", "e3"]):
    #     # Ensure that you only send these functions NNF formulas
    #     # Literals are compiled to NNF here
    #     print(" %s: %.2f" % (vn, likelihood(T, v)))
    print()