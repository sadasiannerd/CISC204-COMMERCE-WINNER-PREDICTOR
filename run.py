
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

E.add_constraint((ProfitabilityLevel(PRODUCT_NAME, 1)&(MarketableLevel(PRODUCT_NAME, 2)))
                 |(ProfitabilityLevel(PRODUCT_NAME,2)&InnovationLevel(PRODUCT_NAME,2))
                 |(InnovationLevel(PRODUCT_NAME, 1)&MarketableLevel(PRODUCT_NAME,2))
                 |(InnovationLevel(PRODUCT_NAME, 2)&MarketableLevel(PRODUCT_NAME,1),ProfitabilityLevel(PRODUCT_NAME, 1))
                 |(ProfitabilityLevel(PRODUCT_NAME, 2)&MarketableLevel(PRODUCT_NAME, 1)))

#Market types
pure_competition = Var(f"{PRODUCT_NAME} is in market Pure Competition")
monopolistic = Var(f"{PRODUCT_NAME} is in market Monopolistic Competition")
monopoly = Var(f"{PRODUCT_NAME} is in market Monopoly")
oligopoly = Var(f"{PRODUCT_NAME} is in market Oligopoly")

E.add_constraint(pure_competition|monopolistic|monopoly|oligopoly)

#Other propositions
seasonal_demand = Var(f"{PRODUCT_NAME} is in seasonal demand")
competitive_price = Var(f"{PRODUCT_NAME} has a competitive price")
unique_product = Var(f"{PRODUCT_NAME} is a unique product")
unique_market = Var(f"{PRODUCT_NAME} is unique in its market")
credible = Var(f"{PRODUCT_NAME} is credible")
saturated = Var(f"{PRODUCT_NAME} is saturated")

#TODO: manually enter other propositions

def complex_constraints():
    #a unique level of 2 means the product has a unique nature and is in a unique market, if it's only true for one of the two then product only has marketable level of 1
    E.add_constraint((unique_market&unique_product)>>MarketableLevel(PRODUCT_NAME, 2))
    E.add_constraint(unique_market>>MarketableLevel(PRODUCT_NAME, 1))
    E.add_constraint(unique_product>>(MarketableLevel(PRODUCT_NAME, 1)&InnovationLevel(PRODUCT_NAME, 1)))

def build_theory():

    #A product can only be in one of the four market types:
    # E.add_constraint(pure_competition >> (~monopolistic & ~monopoly & ~oligopoly)) 
    # E.add_constraint(monopolistic >> ( ~pure_competition & ~monopoly & ~oligopoly))
    # E.add_constraint(monopoly >> (~monopolistic & ~pure_competition & ~oligopoly))
    # E.add_constraint(oligopoly >> (~monopolistic & ~monopoly & ~pure_competition))

    #Pure competition implies product is not able to have a competitive price and competitive marketing (Marketable)
    #In this case means not Marketable_Level_2
    
    E.add_constraint(pure_competition>>(~competitive_price&~MarketableLevel(PRODUCT_NAME,2)))

    #Monopolistic competition is a market involves of innovators, when everyone tries to be different no one is too different

    E.add_constraint(monopolistic>>(~InnovationLevel(PRODUCT_NAME, 2)))

    #Monopoly implies that the market is unique, but price is regulated, so profitable level cannot be 2 and competitive price is set to true
    
    E.add_constraint(monopoly>>(unique_market&~ProfitabilityLevel(PRODUCT_NAME, 2)&competitive_price))

    #Oligopoly implies that the market is small but also involves with innovators, everyone is given with innovation level of 1 but cannot reach to 2

    E.add_constraint(oligopoly>>(InnovationLevel(PRODUCT_NAME, 1)&~InnovationLevel(PRODUCT_NAME, 2)))

    #competitive price means low revenue means low profit margin means profitable level cannot be 2
    E.add_constraint(competitive_price>>~ProfitabilityLevel(PRODUCT_NAME, 2))

    #Seasonal demand implies product is not able to have a competitive price due to everyone else also have a competitive price but doesn't have to market the product
    #Marketable_Level_1
    E.add_constraint(seasonal_demand>>(~competitive_price&MarketableLevel(PRODUCT_NAME,1)))


    return E

if __name__ == "__main__":

    T = build_theory()
    # Don't compile until you're finished adding all your constraints!
    T = T.compile()
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