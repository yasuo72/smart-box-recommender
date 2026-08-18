# What I Learned During This Assignment

The main thing I learned from this assignment is that the simple solution is not always the correct one. At first I thought I could compare the total volume of the products with the volume of the box, but while thinking about different product shapes I realized that this can give wrong results. A long product can have a small volume but still not fit inside a box because of its length.

I also learned how to handle dimensions when an item can be rotated. Instead of writing complicated rotation logic, sorting the three dimensions and comparing them with the sorted box dimensions made the implementation much simpler.

Another thing I learned was that I didn't need to solve the complete 3D bin-packing problem for this assignment. It is a much harder problem, so I used a simpler stacking approach and documented its limitation. This made the solution easier to understand and test.

From the Django side, separating the recommendation logic from the views was useful. I could test the main logic without going through the API every time, and the Django view could stay focused on handling the request and response.

I also learned to not blindly trust AI-generated suggestions. For example, the initial Django version suggested by AI was not compatible with my Python 3.9 environment, so I had to check the actual error and change the Django version. I also found an incorrect test fixture during testing and had to fix it.

Overall, I learned more about checking assumptions, testing edge cases, and making practical trade-offs instead of just trying to build the most complicated solution.
