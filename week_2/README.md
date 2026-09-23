BRIEF 
In this project, I made the cellular automata game of sandbox. Simulating sand, water, rock, fire, smoke and sawdust. Each element has their own properties. What the mouse makes on clicking, changes on pressing the numbers and c clears all cells. The grid is updated frame by frame. The current grid is copied into another variable grid. This new grid is updated with all the changes cell by cell from the bottom. Once all are done, this becomes the old frame and the next frame is calculated next.

Question 1. Why does the swap grid start as a copy of the current state, rather than being
filled with zeros? What would happen to a grain that does not move if G′started empty?

Answer 1. The copy is the next frame that will get updated with all the code being written. It needs to have the past frame's cells already there and then evaluate them cell by cell. it would be more work if we had to evaluate based on the previous frame and then update it in the new frame. Rather now we just evaluate and put it on the same screen. 
That particle would vanish because we would only be copying the changes. The stationary particles wouldn't change and would not be copied over. 

Question 2. Remove the randomised column order and replace it with a fixed left-to-right
scan. Run the simulation for a few hundred ticks. What happens to the shape of a sand pile?
Why?

Answer 2. Uhhh... the final state is similar to the earlier thing. But now particles are more likely go to the right. So the right triangle is made faster and the left one grows slowly. When it reads left to right, it sees the sand, it puts it on the right side as it sees it empty on the next iteration. But the left side has wait until the entire frame is completed before the sand can be pushed to the left side. It'll probably mess more with the fire and smoke particles. 