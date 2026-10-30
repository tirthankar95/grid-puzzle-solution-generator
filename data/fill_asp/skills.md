I will demonstrate to you how to write ASP code for logic grid puzzles.

Let's consider a logic program
In the state of Vermont, a team is compiling an educational guide about some of the indigenous groups that once inhabited the region. Match each indigenous group to their time period, location, and estimated population size. Remember, as with all grid-based logic puzzles, no option in any category will ever be used more than once. If you get stuck or run into problems, try the "Clear Errors" button to remove any mistakes that might be present on the grid, or the "Hint" button to see the next logical step in the puzzle.

Clues:
1.The group located near Lake Champlain was either the group with 6,000 people or the Wabanaki culture.
2.The group located near Burlington didn't have a population size of 7,000.
3.The group founded in 1500 AD was either the group with 4,000 people or the Wabanaki culture.
4.Neither the Abenaki culture nor the society founded in 800 AD was the group located near Burlington.
5.The group with 6,000 people was either the group founded in 1200 AD or the group located near Montpelier.
6.The group with 9,000 people was founded 300 years before the group with 6,000 people.
7.The Wabanaki culture was either the group located near Montpelier or the society founded in 1500 AD.
8.Of the group located near Rutland and the group located near Lake Champlain, one had a population size of 6,000 and the other was the Mohican culture.
9.The Abenaki culture was founded sometime after the group located near Montpelier.

Solve the grid puzzle by filling the table:
+---------+------------+---------------+-------------+
| Years   | Cultures   | Populations   | Locations   |
+=========+============+===============+=============+
| 800 AD  |            |               |             |
+---------+------------+---------------+-------------+
| 1200 AD |            |               |             |
+---------+------------+---------------+-------------+
| 1500 AD |            |               |             |
+---------+------------+---------------+-------------+
| 1800 AD |            |               |             |
+---------+------------+---------------+-------------+

Use the clues to fill the table with the following categories:
Cultures: Abenaki, Mohican, Wabanaki, Algonquin
Populations: 4,000, 6,000, 9,000, 7,000
Locations: Montpelier, Rutland, Burlington, Lake Champlain

# STEP 1
First we define the domain of the logic program, take the 

# STEP 2
Since the dimension 'Years' is already filled in the table we will make the following 
definitions with respect to the dimension 'Years'.
This means a particular year will have a unique culture, note this doesn't mean a particular culture will have a unique year
1 {culture(C,Y): cultures(C)} 1 :- years(Y).

# STEP 3
% Clue 6: The fiberglass kite was either the sled craft or the 4 ft kite.
o5_1 :- material(fiberglass, W), design(sled, W).
o5_2 :- material(fiberglass, W), wingspans(W), W = 4.
:- not 1 {o5_1; o5_2} 1.

The quantity q1 of type T1 was either quantity q2 of type T2 or quantity q3 of type T3. 
T1, T2 and T3 are not reference dimensions.
o1 :- T1(q1, x), T2(q2, X).
o2 :- T1(q1, x), T3(q3, X).
:- not 1 {o1; o2} 1.
where x is the reference dimension. 

The quantity q1 of type T1 was either quantity q2 of type T2 or quantity q3 of type T3. 
T1 and T2 are not reference dimensions, T3 is the reference dimension.
o1 :- T1(q1, x), T2(q2, X).
o2 :- T1(q1, x), T3(X), X = q3.
:- not 1 {o1; o2} 1.
where x is the reference dimension. 


% Clue 4: Of the sled craft and the box kite, one is made of nylon and the other has a 3 ft wingspan.
o4_1 :- design(sled, W1), material(nylon, W1), design(box, W2), wingspans(W2), W2 = 3.
o4_2 :- design(sled, W1), wingspans(W1), W1 = 3, design(box, W2), material(nylon, W2).
:- not 1 {o4_1; o4_2} 1.