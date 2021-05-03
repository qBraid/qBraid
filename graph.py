# -*- coding: utf-8 -*-
"""
Created on Fri Apr 23 12:21:24 2021

@author: Erik
"""

import json
import os
import networkx as nx

def plot_dependency_graph():

    with open('graph.json')as f:
        data = json.load(f)
        
    G = nx.DiGraph()
    T = nx.Graph()
    
    excluded_packages = ('cirq','qiskit','braket','matplotlib','nbformat','numpy','sympy')
    
    for node in data.keys():
        if not node.startswith(excluded_packages):
            G.add_node(node)
       
    # all edges
    for node in G.nodes():
        if 'imports' in data.keys():
            for edge in data[node]['imports']:
                if not node.startswith(excluded_packages):
                    G.add_edge(node,edge)
            
    
    def add_to_dict_if_possible(options, name_to_add):
        if not name_to_add  in options.keys():
            options[name_to_add] = {}
            
    layer_options = {'qbraid':{},'__main__':{}}
    for node in G.nodes:
        layers = node.split('.')
        
        
        options_dict = {}    
        for i,item in enumerate(layers):
            options_dict = options_dict[item]
            #add_to_dict_if_possible(options, name_to_add)
            
            if item not in layer_options[i]:
                layer_options[i].append(item)
    
    print(layer_options)
    
    #print(list(G.nodes()))
    
if __name__=="__main__":
    
    import networkx as nx
    from networkx.drawing.nx_agraph import graphviz_layout
    import matplotlib.pyplot as plt
    G = nx.DiGraph()
    
    G.add_node("ROOT")
    
    for i in range(5):
        G.add_node("Child_%i" % i)
        G.add_node("Grandchild_%i" % i)
        G.add_node("Greatgrandchild_%i" % i)
    
        G.add_edge("ROOT", "Child_%i" % i)
        G.add_edge("Child_%i" % i, "Grandchild_%i" % i)
        G.add_edge("Grandchild_%i" % i, "Greatgrandchild_%i" % i)
    
    # write dot file to use with graphviz
    # run "dot -Tpng test.dot >test.png"
    nx.nx_agraph.write_dot(G,'test.dot')
    
    # same layout using matplotlib with no labels
    plt.title('draw_networkx')
    pos=graphviz_layout(G, prog='dot')
    nx.draw(G, pos, with_labels=False, arrows=False)
    plt.savefig('nx_test.png')
