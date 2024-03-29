# =============================
# Student Names: Devynn Garrow, Jessica Guetre
# Group ID: 13
# Date: January 19, 2024
# =============================
# CISC 352 - W23
# propagators.py
# desc: 
    # Functions to implement forward checking and generalized arc consistency (GAC) propagation for a CSP model.  
    # Function to perform forward checking propagation works for 1) newly assigned variable V: forward check all constraints with V that have one 
    # unassigned variable left and 2) no newly assigned variable: look for unary constraints of the csp and forward check these constraints
    # Function to perform GAC propagation works for 1) newly assigned variable V: perform GA consistency check with all constraints containing V 
    # and 2) no newly assigned variable: perform GA consistency check with with all constaints of the CSP

import itertools

#Look for #IMPLEMENT tags in this file. These tags indicate what has
#to be implemented to complete problem solution.

'''This file will contain different constraint propagators to be used within
   bt_search.

   propagator == a function with the following template
      propagator(csp, newly_instantiated_variable=None)
           ==> returns (True/False, [(Variable, Value), (Variable, Value) ...]

      csp is a CSP object---the propagator can use this to get access
      to the variables and constraints of the problem. The assigned variables
      can be accessed via methods, the values assigned can also be accessed.

      newly_instaniated_variable is an optional argument.
      if newly_instantiated_variable is not None:
          then newly_instantiated_variable is the most
           recently assigned variable of the search.
      else:
          progator is called before any assignments are made
          in which case it must decide what processing to do
           prior to any variables being assigned. SEE BELOW

       The propagator returns True/False and a list of (Variable, Value) pairs.
       Return is False if a deadend has been detected by the propagator.
       in this case bt_search will backtrack
       return is true if we can continue.

      The list of variable values pairs are all of the values
      the propagator pruned (using the variable's prune_value method).
      bt_search NEEDS to know this in order to correctly restore these
      values when it undoes a variable assignment.

      NOTE propagator SHOULD NOT prune a value that has already been
      pruned! Nor should it prune a value twice

      PROPAGATOR called with newly_instantiated_variable = None
      PROCESSING REQUIRED:
        for plain backtracking (where we only check fully instantiated
        constraints)
        we do nothing...return true, []

        for forward checking (where we only check constraints with one
        remaining variable)
        we look for unary constraints of the csp (constraints whose scope
        contains only one variable) and we forward_check these constraints.

        for gac we establish initial GAC by initializing the GAC queue
        with all constaints of the csp


      PROPAGATOR called with newly_instantiated_variable = a variable V
      PROCESSING REQUIRED:
         for plain backtracking we check all constraints with V (see csp method
         get_cons_with_var) that are fully assigned.

         for forward checking we forward check all constraints with V
         that have one unassigned variable left

         for gac we initialize the GAC queue with all constraints containing V.
   '''

def prop_BT(csp, newVar=None):
    '''Do plain backtracking propagation. That is, do no
    propagation at all. Just check fully instantiated constraints'''

    if not newVar:
        return True, []
    for c in csp.get_cons_with_var(newVar):
        if c.get_n_unasgn() == 0:
            vals = []
            vars = c.get_scope()
            for var in vars:
                vals.append(var.get_assigned_value())
            if not c.check_tuple(vals):
                return False, []
    return True, []

def prop_FC(csp, newVar=None):
    '''Do forward checking. That is check constraints with
       only one uninstantiated variable. Remember to keep
       track of all pruned variable,value pairs and return '''
    #IMPLEMENT
    prunedVals = []
    
    if newVar != None:
        cons = csp.get_cons_with_var(newVar)
        for c in cons:
            if c.check_var_val(newVar, newVar.get_assigned_value()) == False:
                return False, prunedVals
            if c.get_n_unasgn() == 1:
                var = c.get_scope()[0]
                vals = var.cur_domain()
                varPrunedVals = []
                for val in vals:
                    if c.check_var_val(var, val) == False:
                        var.prune_value(val)
                        varPrunedVals.append(val)                    
                        
                # Check if the domain of the constrained node is empty
                # this means that this value causes constraint violation
                if var.cur_domain_size() == 0:
                    for val in varPrunedVals:
                        var.unprune_value(val)
                    return False, prunedVals

                # Variable assignment satisfies constraint, include pruned values
                for val in varPrunedVals:
                    prunedVals.append((var, val))

                        
    else:
        cons = csp.get_all_nary_cons(1)
        for c in cons:
            var = c.get_scope()[0]
            vals = var.cur_domain()
            varPrunedVals = []
            for val in vals:
                var.assign(val)
                forward_prop = prop_FC(csp, var)
                if forward_prop[0] == False:
                    var.unassign()
                    var.prune_value(val)
                    varPrunedVals.append(val)
                    
                for pair in forward_prop[1]:
                    prunedVals.append(pair)
            prunedVals.append((var, varPrunedVals))

            # Check if none of the values are valid (unary constraint is impossible)
            if var.cur_domain_size() == 0:
                for val in varPrunedVals:
                    var.unprune_value(val)
                return False, prunedVals
    return True, prunedVals


def prop_GAC(csp, newVar=None):
    '''Do GAC propagation. If newVar is None we do initial GAC enforce
       processing all constraints. Otherwise we do GAC enforce with
       constraints containing newVar on GAC Queue'''
    #IMPLEMENT
    prunedVals = []
    arcs = []

    # Initialize constraints and check to ensure that new assignment is valid
    if newVar != None:
        cons = csp.get_cons_with_var(newVar)
        for c in cons:
             if c.check_var_val(newVar, newVar.get_assigned_value()) == False:
                    return False, prunedVals
    else:
        cons = csp.get_all_cons()

    # Initialize all arcs for constraints
    arcs = []
    for c in cons:
        scope = c.get_scope()
        for var in scope:
            otherVars = []
            for v in scope:
                if v != var:
                    otherVars.append(v)
            arcs.append((var,c, otherVars))

    # Check consistency of each arc
    while len(arcs) > 0:
        currentArc = arcs[0]
        arcs.remove(currentArc)

        var = currentArc[0]
        con = currentArc[1]
        otherVars = currentArc[2]
        domainX = []
        for xi in otherVars:
            domainX.append(xi.cur_domain())
            
        combos = list(itertools.product(*domainX)) # gives all possible combinations of other variable values

        varDomain = var.cur_domain()
        varPrunedVals = []

        # Checks each value in domain of variable to check if there are possible solutions
        for val in varDomain:
            if con.check_var_val(var, val) == False: # There are no current satisfying tuples in this constraint
                var.prune_value(val)
                varPrunedVals.append(val)

                # Add constraints that have var in them
                consWithVar = csp.get_cons_with_var(var)
                for cWithVar in consWithVar:
                    scope = cWithVar.get_scope()
                    for cVar in scope:
                        otherVars = []
                        if cVar != var:
                            for v in scope:
                                if v != cVar:
                                    otherVars.append(v)
                            newArc = (cVar,cWithVar, otherVars)
                            if newArc not in arcs:
                                arcs.append(newArc)     

                # Check if the domain of the constrained node is empty
                # this means that this value causes constraint violation
                if var.cur_domain_size() == 0:
                    for val in varPrunedVals:
                        var.unprune_value(val)
                    return False, prunedVals
        
        # Variable assignment satisfies constraint, include pruned values and update constraints to check
        for val in varPrunedVals:
            prunedVals.append((var, val))        
            
    return True, prunedVals
        