from flask import Flask, render_template, request
from graphviz import Digraph
import os
import copy

app = Flask(__name__)

class DFA:
    def __init__(self, states, alphabets, init_state, final_states, transition_funct):
        self.states = states
        self.alphabets = alphabets
        self.init_state = init_state
        self.final_states = final_states
        self.transition_funct = transition_funct
        self.ds = {}
        self.transition_dict = {}
        self.set_transition_dict()

    def draw_graph(self, name):
        gr = Digraph(format='svg')
        gr.attr(rankdir='LR')  # Make the graph horizontal
        gr.attr('node', shape='point')
        gr.node('qi')
        for i in self.states:
            if i in self.final_states:
                gr.attr('node', shape='doublecircle', color='green', style='')
            elif i in self.init_state:
                gr.attr('node', shape='circle', color='black', style='')
            else:
                gr.attr('node', shape='circle', color='black', style='')
            gr.node(str(i))
            if i in self.init_state:
                gr.edge('qi', str(i), 'start')
        for k1, v1 in self.transition_dict.items():
            for k2, v2 in v1.items():
                if str(v2) != 'ϕ':
                    gr.edge(str(k1), str(k2), str(v2))
        output_path = os.path.join('static', f'{name}.svg')
        gr.render(output_path.replace('.svg', ''), cleanup=True)
        return f'{name}.svg'

    def set_transition_dict(self):
        dict_states = {r: {c: 'ϕ' for c in self.states} for r in self.states}
        for i in self.states:
            for j in self.states:
                indices = [ii for ii, v in enumerate(self.transition_funct[i]) if v == j]
                if len(indices) != 0:
                    valid_indices = [v for v in indices if v < len(self.alphabets)]
                    if valid_indices:
                        dict_states[i][j] = '+'.join([str(self.alphabets[v]) for v in valid_indices])
                    else:
                        dict_states[i][j] = 'ϕ'  # Or handle invalid case here
        self.ds = dict_states
        self.transition_dict = copy.deepcopy(dict_states)

    def get_intermediate_states(self):
        return [state for state in self.states if state not in ([self.init_state] + self.final_states)]

    def simplify_regex(self, regex):
        regex = regex.replace('+ϕ', '').replace('ϕ+', '').replace('(ϕ)', '').replace('()', '')
        # Remove duplicate terms (basic optimization)
        parts = sorted(set(regex.split('+')))
        return '+'.join(parts)

    def toregex(self):
        intermediate_states = self.get_intermediate_states()
        dict_states = self.ds

        for inter in intermediate_states:
            predecessors = [key for key, value in dict_states.items() if value.get(inter, 'ϕ') != 'ϕ' and key != inter]
            successors = [key for key, value in dict_states[inter].items() if value != 'ϕ' and key != inter]
            inter_loop = dict_states[inter].get(inter, 'ϕ') if dict_states[inter].get(inter, 'ϕ') != 'ϕ' else ''

            for i in predecessors:
                for j in successors:
                    new_transition = f"({dict_states[i][inter]})({inter_loop})*({dict_states[inter][j]})"
                    if dict_states[i][j] != 'ϕ':
                        dict_states[i][j] = f"({dict_states[i][j]})+{new_transition}"
                    else:
                        dict_states[i][j] = new_transition
                    dict_states[i][j] = self.simplify_regex(dict_states[i][j])

            dict_states = {r: {c: v for c, v in val.items() if c != inter} for r, val in dict_states.items() if r != inter}

        print(f"Final Transition Dictionary: {dict_states}")

        init_loop = dict_states.get(self.init_state, {}).get(self.init_state, 'ϕ')
        final_expressions = []
        for final_state in self.final_states:
            final_path = dict_states.get(self.init_state, {}).get(final_state, 'ϕ')
            if final_path != 'ϕ':
                final_path = f"({final_path})"
                final_loop = f"({dict_states.get(final_state, {}).get(final_state, 'ϕ')})*" if dict_states.get(final_state, {}).get(final_state, 'ϕ') != 'ϕ' else ''
                final_expressions.append(f"{init_loop}{final_path}{final_loop}")

        return self.simplify_regex('+'.join(final_expressions))



@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        states = request.form['states'].split()
        alphabets = request.form['alphabets'].split()
        init_state = request.form['init_state']
        final_states = request.form['final_states'].split()
        transition_funct = {
            state: request.form[f'transitions_{state}'].split()
            for state in states
        }
        dfa = DFA(states, alphabets, init_state, final_states, transition_funct)
        graph_name = dfa.draw_graph("dfa")
        regex = dfa.toregex()
        return render_template('index.html', graph=graph_name, regex=regex)

    return render_template('index.html', graph=None, regex=None )


if __name__ == '__main__':
    app.run(debug=True)
