from pulp import *

def optimize_sprint_planning():
    # Datu sagatavošana
    sprint_capacities = {1: 20, 2: 30, 3: 35, 4: 35, 5: 20}

    user_stories = {
        'R01': {'U': 80, 'P': 9, 'r': 2.0, 'a': 0.3, 'Y': ['R02', 'R47']},
        'R02': {'U': 85, 'P': 9, 'r': 2.0, 'a': 0.2, 'Y': ['R14']},
        'R06': {'U': 45, 'P': 4, 'r': 1.3, 'a': 0.0, 'Y': []},
        'R07': {'U': 50, 'P': 5, 'r': 1.3, 'a': 0.2, 'Y': ['R08']},
        'R08': {'U': 20, 'P': 4, 'r': 1.0, 'a': 0.0, 'Y': []},
        'R09': {'U': 35, 'P': 5, 'r': 1.0, 'a': 0.1, 'Y': ['R10']},
        'R10': {'U': 50, 'P': 4, 'r': 1.3, 'a': 0.0, 'Y': []},
        'R12': {'U': 85, 'P': 8, 'r': 1.7, 'a': 0.4, 'Y': ['R14']},
        'R14': {'U': 80, 'P': 7, 'r': 1.7, 'a': 0.0, 'Y': []},
        'R15': {'U': 60, 'P': 6, 'r': 1.3, 'a': 0.2, 'Y': ['R16', 'R17']},
        'R16': {'U': 60, 'P': 8, 'r': 1.7, 'a': 0.0, 'Y': []},
        'R17': {'U': 25, 'P': 2, 'r': 1.0, 'a': 0.0, 'Y': []},
        'R18': {'U': 30, 'P': 3, 'r': 1.3, 'a': 0.1, 'Y': ['R19']},
        'R19': {'U': 20, 'P': 4, 'r': 1.0, 'a': 0.0, 'Y': []},
        'R20': {'U': 10, 'P': 7, 'r': 1.0, 'a': 0.0, 'Y': []},
        'R47': {'U': 75, 'P': 5, 'r': 1.7, 'a': 0.3, 'Y': ['R48']},
        'R48': {'U': 60, 'P': 7, 'r': 1.3, 'a': 0.3, 'Y': ['R49']},
        'R49': {'U': 80, 'P': 6, 'r': 1.7, 'a': 0.4, 'Y': ['R50']},
        'R50': {'U': 70, 'P': 8, 'r': 1.7, 'a': 0.0, 'Y': []},
        'R51': {'U': 55, 'P': 6, 'r': 1.3, 'a': 0.2, 'Y': ['R52']},
        'R52': {'U': 30, 'P': 6, 'r': 1.0, 'a': 0.0, 'Y': []}
    }

    # Atkarības starp stāstiem (D_j)
    dependencies = {
        'R02': ['R01'],  # R02 nevar izpildīt bez R01
        'R14': ['R02'],  # R14 nevar izpildīt bez R02
    }

    # Bāzes modelis
    base_model = LpProblem("Bāzes_modelis", LpMaximize)
    
    # Mainīgie
    x_base = LpVariable.dicts("x_base", 
                            [(i, j) for i in sprint_capacities.keys() 
                                    for j in user_stories.keys()],
                            0, 1, LpBinary)
    
    # Mērķa funkcija
    base_model += lpSum(user_stories[j]['U'] * user_stories[j]['r'] * x_base[(i,j)] 
                       for i in sprint_capacities.keys() 
                       for j in user_stories.keys())
    
    # Ierobežojumi
    for i in sprint_capacities.keys():
        base_model += lpSum(user_stories[j]['P'] * x_base[(i,j)] 
                          for j in user_stories.keys()) <= sprint_capacities[i]
        
    for j in user_stories.keys():
        base_model += lpSum(x_base[(i,j)] 
                         for i in sprint_capacities.keys()) == 1
    
    base_model.solve()
    base_utility = value(base_model.objective)

    # Pilnais modelis
    full_model = LpProblem("Pilnais_modelis", LpMaximize)
    
    # Mainīgie
    x = LpVariable.dicts("x", 
                        [(i, j) for i in sprint_capacities.keys() 
                                for j in user_stories.keys()],
                        0, 1, LpBinary)
    
    y = LpVariable.dicts("y",
                        [(i, j) for i in sprint_capacities.keys()
                                for j in user_stories.keys()],
                        0, None, LpInteger)
    
    # Mērķa funkcija
    full_model += lpSum(
        user_stories[j]['U'] * (
            user_stories[j]['r'] * x[(i,j)] +
            user_stories[j]['a'] * y[(i,j)] / max(1, len(user_stories[j]['Y']))
        )
        for i in sprint_capacities.keys()
        for j in user_stories.keys()
    )
    
    # Visi ierobežojumi
    for i in sprint_capacities.keys():
        full_model += lpSum(user_stories[j]['P'] * x[(i,j)] 
                          for j in user_stories.keys()) <= sprint_capacities[i]
    
    for j in user_stories.keys():
        full_model += lpSum(x[(i,j)] 
                         for i in sprint_capacities.keys()) == 1
    
    for j, deps in dependencies.items():
        for i in sprint_capacities.keys():
            full_model += lpSum(x[(k,d)] 
                             for k in range(1, i+1)
                             for d in deps) >= x[(i,j)] * len(deps)
    
    for j in user_stories.keys():
        if user_stories[j]['Y']:
            for i in sprint_capacities.keys():
                full_model += y[(i,j)] <= lpSum(x[(i,k)] 
                                              for k in user_stories[j]['Y'])
                full_model += y[(i,j)] <= len(user_stories[j]['Y']) * x[(i,j)]
    
    full_model.solve()
    full_utility = value(full_model.objective)

    # Rezultātu apstrāde un analīze
    if LpStatus[full_model.status] == 'Optimal':
        print("="*50)
        print("OPTIMĀLIE REZULTĀTI")
        print("="*50)
        
        # Pilnā modeļa rezultāti
        solution = {}
        for i in sprint_capacities.keys():
            stories = [j for j in user_stories.keys() if x[(i,j)].varValue == 1]
            points = sum(user_stories[j]['P'] for j in stories)
            solution[f"Sprint {i}"] = {
                'stories': stories,
                'points': points,
                'capacity': sprint_capacities[i]
            }
            
            print(f"\nSprint {i} ({points}/{sprint_capacities[i]} punkti):")
            print("-"*30)
            for j in stories:
                deps = ", ".join(dependencies.get(j, ["nav"]))
                related = ", ".join(user_stories[j]['Y']) if user_stories[j]['Y'] else "nav"
                print(f"{j}: Atkarības={deps}, Radniecīgie={related}")
        
        # Salīdzinošā analīze
        print("\n" + "="*50)
        print("SALĪDZINOŠĀ ANALĪZE")
        print("="*50)
        
        improvement = ((full_utility - base_utility)/base_utility)*100
        print(f"\nBāzes modeļa lietderība: {base_utility:.2f}")
        print(f"Pilnā modeļa lietderība: {full_utility:.2f}")
        print(f"Uzlabojums: {improvement:.2f}%")
        
        return {
            'base_utility': base_utility,
            'full_utility': full_utility,
            'solution': solution,
            'improvement': improvement
        }
    else:
        print("Optimālais risinājums nav atrasts.")
        return None

if __name__ == "__main__":
    results = optimize_sprint_planning()