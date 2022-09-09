# PSHomeroomPopulation

Script to automatically populate the home_room and homeroom_number fields on student profiles with the name of the teacher for thier homeroom class (or whatever class Pre-K is enrolled in) as well as the number of the classroom it takes place in.
Looks through the cc (courses) table in order to find all their classes, filters to just ones that could be homerooms (for 6-12) or their only class for K-5..
Also blanks out inactive students or students who are no longer enrolled in classes instead of the previous solution which left it in place.
