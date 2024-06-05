"""
6.1010 Lab 4:
Snekoban Game
"""

import json
import typing

# NO ADDITIONAL IMPORTS!


direction_vector = {
    "up": (-1, 0),
    "down": (+1, 0),
    "left": (0, -1),
    "right": (0, +1),
}


def make_new_game(level_description):
    """
    Given a description of a game state, create and return a game
    representation of your choice.

    The given description is a list of lists of lists of strs, representing the
    locations of the objects on the board (as described in the lab writeup).

    For example, a valid level_description is:

    [
        [[],                   ['wall'],     ['computer']],
        [['target', 'player'], ['computer'], ['target']],
    ]

    The exact choice of representation is up to you; but note that what you
    return will be used as input to the other functions.

    Description:
    Level_description is converted into a static grid for non-movables (targets, cpus)
    Dynamic objects, computer/player are stored as a frozenset, and tuple respectively

    sets of flag locations also stored as a set for victory check
    """
    static_grid = [] #list of lists
    box_positions = set() #their order in relation doesnt matter
    target_positions = set() #order doesnt matter
    num_boxes = 0
    num_targets = 0
    #Iterate through entire level desc
    for row, cols_in_row in enumerate(level_description):
        static_row = []
        for col, items in enumerate(cols_in_row):
            #Build 2D static grid for non-movables
            if 'wall' in items:
                static_row.append('W')
            elif 'target' in items:
                static_row.append('T')
                target_positions.add((row,col))

                num_targets += 1
            else:
                static_row.append('.')

            #track pos for dynamic objects
            if 'player' in items:
                player_position = (row, col)
            if 'computer' in items:
                box_positions.add((row, col))
                num_boxes += 1

        static_grid.append(static_row) #add translated row

    game_state = {
        "static_grid": static_grid,
        "player_position": player_position,
        "box_positions": frozenset(box_positions), #need to be hashable
        "target_positions": frozenset(target_positions), #need to be hashable
        "num_boxes": num_boxes,
        "num_targets": num_targets,

    }

    return game_state


def victory_check(game):
    """
    Given a game representation (of the form returned from make_new_game),
    return a Boolean: True if the given game satisfies the victory condition,
    and False otherwise.
    """

    return game["num_boxes"] != 0 and (game["box_positions"] == game["target_positions"])

#CHECKING IF MOVE IS LEGAL FUNCTIONS
def object_blocks_box(game, direction):
    """Returns true if there is a an object (wall/box) blocking the box the player
    tries to move
    Inner cell refers to the cell directly on the spot the player is trying to move onto
    Pot outer box is the loc of where there might be an additional blocking box behind
    the inner box
    """
    static_grid = game["static_grid"]
    potential_outer_box = cell_info(game,direction)["out_cell"]

    #row, col of potential outer box
    y,x = potential_outer_box

    #Is there a wall or box where the adjacent box wants to move?
    return (potential_outer_box in game["box_positions"]) or (static_grid[y][x] == "W")


def cell_info(game, direction):
    """Returns the position of possible boxes of interest.

    Args:
        game (dict): representation of the current game state
        direction (_type_): direction to increment object position
    """

    #The adj box will be in the same spot as if the
    #player had moved into it
    adj_cell = get_new_player_pos(game, direction)

    return{
        "adj_cell": adj_cell,
        "out_cell": increment_pos(adj_cell, direction) #increment 1 in dir
    }

def box_blocks_player(game, direction):
    """Returns True if a box is preventing a player from moving into it,
        whether it be from a wall or another box being behind the box"""
    box_positions = game["box_positions"]
    new_player_pos = get_new_player_pos(game, direction)

    if new_player_pos in box_positions: #Box is on the spot a player is moving into
        #check if a box is preventing that box from moving
        return object_blocks_box(game, direction)

    return None

def wall_blocks_player(game, new_player_pos):
    """Will return True if a wall is already
        on the new player position"""

    static_grid = game["static_grid"]
    y, x = new_player_pos

    return static_grid[y][x] == "W" #returns false otherwise

def get_new_player_pos(game, direction):
    return increment_pos(game["player_position"], direction)

def increment_pos(object_pos, direction):
    """returns a new object position with the incremented direction"""
    shift = direction_vector[direction]
    new_pos = tuple(sum(coords) for coords in zip(object_pos, shift))

    return new_pos

def can_move(game, direction):
    """Checks if it is legal to move the player in a given direction"""

    new_player_pos = get_new_player_pos(game, direction)

    #flip returning boolean because funcs return true if illegal
    return not (wall_blocks_player(game, new_player_pos) or
            box_blocks_player(game,direction))
#END OF MOVE LEGAL FUNCTIONS

def new_box_positions(game, direction):
    """Returns new sets of box positions if the boxes move
    Positions refers to pos to remove and to add"""
    old_box_pos = cell_info(game,direction)["adj_cell"]
    new_box_pos = cell_info(game,direction)["out_cell"]

    box_positions = set(game["box_positions"])

    box_positions.discard(old_box_pos)
    box_positions.add(new_box_pos)

    return box_positions

def step_game(game, direction):
    """
    Given a game representation (of the form returned from make_new_game),
    return a new game representation (of that same form), representing the
    updated game after running one step of the game.  The user's input is given
    by direction, which is one of the following:
        {'up', 'down', 'left', 'right'}.

    This function should not mutate its input.
    """

    if box_blocks_player(game, direction) is False: #if boxes move
        boxes = new_box_positions(game, direction)

    else: #boxes dont move
        boxes = game["box_positions"]

    if can_move(game,direction):
        return {
        "static_grid": game["static_grid"],
        "player_position": get_new_player_pos(game,direction), #move is legal
        'box_positions': boxes, #may or not move
        "target_positions": game["target_positions"],
        "num_boxes": game["num_boxes"],
        "num_targets": game["num_targets"],
        }
    else:
        return game


def dump_game(game):
    """
    Given a game representation (of the form returned from make_new_game),
    convert it back into a level description that would be a suitable input to
    make_new_game (a list of lists of lists of strings).

    This function is used by the GUI and the tests to see what your game
    implementation has done, and it can also serve as a rudimentary way to
    print out the current state of your game for testing and debugging on your
    own.
    """
    static_grid = game["static_grid"]

    #iterates through the entire game rep
    level_description = []
    for row, contents in enumerate(static_grid):
        row_contents = []
        for col, item in enumerate(contents):
            col_contents = []

            #switches content to desired level_desc implementation
            if item == "W":
                col_contents.append("wall")
            elif item == "T":
                col_contents.append("target")

            #checks if we are at the desired row,col to insert player/boxes
            if (row,col) == game["player_position"]:
                col_contents.append("player")
            if (row, col) in game["box_positions"]:
                col_contents.append("computer")
            row_contents.append(col_contents)
        level_description.append(row_contents)

    return level_description


def neighbors_function(terminal_state, game):
    """Returns a list of legal states for a given input state and static info
    THIS DOES NOT RETURN ENTIRE GAME REPS
    RATHER ONLY DYNAMIC INFO SUCH AS
    COMPUTER AND PLAYER LOCATIONS

    also stores action for solving"""


    player_position, box_positions = terminal_state #for readability unpack tuple

    #Here some info is static so we just assign it to original
    game = {
        "static_grid": game["static_grid"],
        "player_position": player_position,
        "box_positions": box_positions,
        "target_positions": game["target_positions"],
        "num_boxes": game["num_boxes"],
        "num_targets": game["num_targets"],
    }


    valid_states = []
    for direction in direction_vector: #go thru each direction possible
        if can_move(game,direction): #if its legal add that new state to neighbors
            new_game = step_game(game,direction)
            valid_states.append((
                (new_game["player_position"],frozenset(new_game["box_positions"])),
                                 direction))
    return valid_states




def solve_puzzle(game):
    """
    Given a game representation (of the form returned from make_new_game), find
    a solution.

    Return a list of strings representing the shortest sequence of moves ("up",
    "down", "left", and "right") needed to reach the victory condition.

    If the given level cannot be solved, return None.
    """
    #pretty standard path finding algo from reading with modified action handling

    #if game already solved
    if victory_check(game):
        return[]

    #starting state is a tuple of position and fset of box positions
    starting_state = (game["player_position"], game["box_positions"])

    visited = {starting_state} #keep track of visited to not repeat

    #queue of tuples containing (actions, state)
    agenda = [([], starting_state)]



    while agenda:
        actions, terminal_state = agenda.pop(0) #take first in queue

        #neighbor is player and box pos, dir is dir
        for (neighbor,direction) in neighbors_function(terminal_state, game):


            if neighbor not in visited: #if valid new step
                new_actions = actions + [direction] #add its action
                new_path = (new_actions, neighbor)
                #path is a tuple of actions and game state

                victory_check_rep = {
                    "target_positions": game["target_positions"], #static
                    "box_positions": neighbor[1], #boxes are at neighbor index 1
                    "num_boxes": game["num_boxes"], #static
                    "num_targets": game["num_targets"], #static
                }
                if victory_check(victory_check_rep):
                    return new_actions

                agenda.append(new_path)
                visited.add(neighbor)

    return None







if __name__ == "__main__":
    # Assuming you have JSON text stored in a file
    json_file_path = '/Users/autumn/Desktop/snekoban/puzzles/s2_050.json'

    # Read the JSON text from the file
    with open(json_file_path, 'r') as file:
        json_text = file.read()

    # Parse the JSON text
    cheese = make_new_game(json.loads(json_text))

    print(solve_puzzle(cheese))
