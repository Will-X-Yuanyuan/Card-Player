# This is the main card playing module, which decides the play based on many factors 
# including the table state, card history, hand, number of cards played and so on

from itertools import groupby
from collections import defaultdict as dd
from itertools import combinations 
from sys import exit
from phase_type import * 
from valid_play import *

# constants
PLAY_ONE = 1
PLAY_TWO = 2
PLAY_THREE = 3
PLAY_FOUR = 4
PLAY_FIVE = 5  # the PLAYs indicate the type of play
PHASE_ONE = 1
PHASE_TWO = 2
PHASE_THREE = 3
PHASE_FOUR = 4
PHASE_FIVE = 5
PHASE_SIX = 6
PHASE_SEVEN = 7
CARD_VALUES = {'A': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, 
               '9': 9, '0': 10, 'J': 11, 'Q': 12, 'K': 13}
RED = 'HD'     # HD - hearts and diamonds
BLACK = 'CS'   # CS - clubs and spades
MIN_NATURAL = 2  # min number of natural cards in a play (except accumulations)
MAX_RUN = 12
ACCUMULATION_SEQUENCE = [34, 55, 68, 76, 81, 84, 86, 87, 88]
ACCUM_34 = 34


def phazed_play(player_id, table, turn_history, phase_status, hand, discard):
    '''Returns a play based on the situation of the table, and the plays
    that have been done so far. The play is a 2 tuple describing the single
    play.
    Gives error if the returned play is not valid
    '''
    table_phase = table[player_id][0]
    curr_phase = phase_status[player_id] + 1
    
    # First, check whether it is the start of the turn. If it is, execute
    # a pickup play
    # Check that it is not the first turn in the hand:
    if turn_history:
        last_player = turn_history[-1][0]
        if last_player != player_id:
            play = pickup_play(player_id, table, turn_history, phase_status, hand, discard)
            if not phazed_is_valid_play(play, player_id, table, turn_history, phase_status, hand, discard):
                print('ERROR: invalid play!')
                exit()
            else:
                return play
    if not turn_history:
        play = pickup_play(player_id, table, turn_history, phase_status, hand, discard)
        if not phazed_is_valid_play(play, player_id, table, turn_history, phase_status, hand, discard):
                print('ERROR: invalid play!')
                exit()
        else:
            return play

    # Then, check if a phase has been played. If it hasn't, try to execute
    # a phase play
    if not table_phase:
        poss_play = possible_phase(player_id, phase_status, hand)
        if poss_play:
            play = (PLAY_THREE, (curr_phase, poss_play))
            if not phazed_is_valid_play(play, player_id, table, turn_history, phase_status, hand, discard):
                print('ERROR: invalid play!')
                exit()
            else:
                return play
    
    # If none of the above were executed, check if a table play is possible
    if table_phase:
        for i in range(len(table)):
            phase_play = table[i]
            target_phase = phase_play[0]
            for card in hand:
                if target_phase and check_phase(phase_play[1], card, target_phase):
                    tup = (i,) + check_phase(phase_play[1], card, target_phase)
                    play = (PLAY_FOUR, (card, tup))
                    if not phazed_is_valid_play(play, player_id, table, turn_history, phase_status, hand, discard):
                        print('ERROR: invalid play!')
                        exit()
                    else:
                        return play
    
    # Finally, discard if no other plays are possible
    return discard_play(player_id, table, turn_history, 
                        phase_status, hand, discard)


def pickup_play(player_id, table, turn_history, phase_status, hand, discard):
    '''At the start of the turn, determines whether it's better to draw a card 
    from the deck, or to draw a card from the discard pile, based on the 
    current hand, the table etc. 
    Returns a 2 tuple corresponding to the play types 1 and 2.'''
    # Check that there is a discard pile
    if not discard:
        return (PLAY_ONE, None)
    # If phase play is possible, check the table to see if the card on the 
    # discard pile will help with playing a card to the table, or playing a 
    # card to my own phase after I play it
    table_phase = table[player_id][0]
    curr_phase = phase_status[player_id] + 1
    if not table_phase:
        if possible_phase(player_id, phase_status, hand):
            my_phase = possible_phase(player_id, phase_status, hand)
            if check_phase(my_phase, discard, curr_phase):
                return (PLAY_TWO, discard)
            for i in range(len(table)):
                phase_play = table[i]
                tar_phase = phase_play[0]
                if (tar_phase and 
                    check_phase(phase_play[1], discard, tar_phase)):
                    return (PLAY_TWO, discard)
        # If phase play not possible, check the discard pile to see if the 
        # card will allow me to play a phase. If not, then pickup from deck
        else:
            pickup_hand = hand.copy()
            pickup_hand.append(discard)
            if possible_phase(player_id, phase_status, pickup_hand):
                return (PLAY_TWO, discard)
            else:
                return (PLAY_ONE, None)
    # if I have already played my phase, check the discard pile too
    if table_phase:
        for i in range(len(table)):
            phase_play = table[i]
            tar_phase = phase_play[0]
            if tar_phase and check_phase(phase_play[1], discard, tar_phase):
                return (PLAY_TWO, discard)
    
    # if none of the above, then check the value of the discard, take if low
    if CARD_VALUES[discard[0]] <= 6:
        return (PLAY_TWO, discard)
    return (PLAY_ONE, None)


def discard_play(player_id, table, turn_history, phase_status, hand, discard):
    '''discard a card that is probably not useful for the current phase.'''
    table_phase = table[player_id][0]
    curr_phase = phase_status[player_id] + 1
    discard_hand = hand.copy()
    # first check whether I have played a phase. If not, then try to keep the
    # cards that are useful to playing the phase
    if not table_phase:
        
        # for the first phase, try to keep cards of the same value
        if curr_phase == PHASE_ONE:
            duplicates = groupby_values(hand)
            for card in duplicates:
                discard_hand.remove(card)
        
        # for the second phase, try to keep the most frequent suit
        if curr_phase == PHASE_TWO:
            freq_dict = dd(int)
            # Aces are not counted in the freq_dict, as they stand for all suit
            for card in hand:
                if card[0] != 'A':
                    freq_dict[card[1]] += 1
            
            # Consider the possibility of multiple suits being most frequent
            most_freq_suit = max(freq_dict, key=lambda x: freq_dict[x])
            freq_list = []
            for suit, freq in freq_dict.items():
                if suit == most_freq_suit:
                    freq_list.append(suit)
            for card in hand:
                if card[1] in freq_list:
                    discard_hand.remove(card)
        
        # for the third phase, discard Aces if they exist as they barely help
        # with accumulations, and are high scoring. Then calculate the sum
        # of the cards, if the sum is less than 68, discard the smallest value
        # card
        if curr_phase == PHASE_THREE:
            for card in hand:
                if card[0] == 'A':
                    return (PLAY_FIVE, card)
            card_sum = sum(CARD_VALUES[x[0]] for x in hand)
            if card_sum <= ACCUM_34 * 2:
                sorted_hand = sorted(hand, key=lambda x: CARD_VALUES[x[0]])
                return (PLAY_FIVE, sorted_hand[0])
                
        # for the fourth phase, try to keep cards of same value
        if curr_phase == PHASE_FOUR:
            duplicates = groupby_values(hand)
            for card in duplicates:
                discard_hand.remove(card)
        
        # for the fifth phase, try to get rid of duplicate cards of same value
        # but keep Aces
        if curr_phase == PHASE_FIVE:
            duplicates = groupby_values(hand)
            for card in duplicates:
                if card[0] != 'A':
                    return (PLAY_FIVE, card)
        
        # for the sixth phase, discard Aces if they exist. Then, check the sum
        # for each color, if the sum is bigger than 38 (arbitrary value that's
        # bigger than 34), then keep cards of that color if possible
        if curr_phase == PHASE_SIX:
            for card in hand:
                if card[0] == 'A':
                    return (PLAY_FIVE, card)
            color_dict = dd(list)
            for card in hand:
                if card[1] in BLACK:
                    color_dict[BLACK].append(card)
                else:
                    color_dict[RED].append(card)
            sum_black = sum(CARD_VALUES[x[0]] for x in color_dict[BLACK])
            sum_red = sum(CARD_VALUES[x[0]] for x in color_dict[RED])
            if sum_black >= ACCUM_34 + 4:
                for card_b in color_dict[BLACK]:
                    discard_hand.remove(card_b)
            if sum_red >= ACCUM_34 + 4:
                for card_r in color_dict[RED]:
                    discard_hand.remove(card_r)
            
            sorted_discard = sorted(discard_hand, 
                                    key=lambda x: CARD_VALUES[x[0]])
            # check that sorted_discard is not empty. If it is not empty then
            # discard the lowest value card
            if sorted_discard:
                return (PLAY_FIVE, sorted_discard[0])
            if not sorted_discard:
                hand_discard = sorted(hand, key=lambda x: CARD_VALUES[x[0]])
                return (PLAY_FIVE, hand_discard[0])
            
        # for the last phase, keep cards of the same value
        if curr_phase == PHASE_SEVEN:
            duplicates = groupby_values(hand)
            for card in duplicates:
                discard_hand.remove(card)
    
    # in discard_hand, try to keep ACES if possible
    for card in discard_hand:
        if card[0] == 'A':
            discard_hand.remove(card)
    sorted_discard = sorted(discard_hand, key=lambda x: CARD_VALUES[x[0]])
    if not sorted_discard:
        return (PLAY_FIVE, hand[0]) 
    return (PLAY_FIVE, sorted_discard[-1])
    
    
def check_phase(phase, card, target_phase):
    '''Checks whether a card can be played onto a group of cards, for the 
    phase determined by target_phase. Returns the index position of the group
    that the card should be played to, but in the case of phase 5, returns the
    index position of the card within the group that the card should be palyed 
    to. Returns False if not possible.'''
    if target_phase == PHASE_ONE or target_phase == PHASE_FOUR:
        for i in range(len(phase)):
            group = phase[i]
            group.append(card)
            if same_value(group):
                return (i, 0)
    
    if target_phase == PHASE_TWO:
        for i in range(len(phase)):
            group = phase[i]
            group.append(card)
            if same_suit(group):
                return (i, 0)
    
    # For a run, a card can only be inserted to the front or the end of the run
    if target_phase == PHASE_FIVE:
        group = phase[0]
        for i in [0, len(group)]:
            group_copy = group.copy()
            group_copy.insert(i, card)
            if run(group_copy):
                return (0, i)
    
    if target_phase == PHASE_SEVEN:
        group0 = phase[0]
        for i in [0, len(group0)]:
            group_copy = group0.copy()
            group_copy.insert(i, card)
            if run(group_copy) and same_color(group_copy):
                return (0, i)
        group1 = phase[1]
        group1.append(card)
        if same_value(group1):
            return (1, 0)
    return False
    
def possible_phase(player_id, phase_status, hand):
    '''Returns a possible phase play as a list of cards.
    If phase play is not possible, return False.'''
    curr_phase = phase_status[player_id] + 1
    
    # if curr_phase is phase 1, check whether the phase is playable
    if curr_phase == PHASE_ONE:
        new_hand = groupby_values(hand)
        group_len = 3  # length of a group of cards in phase 1
        if possible_values_play(new_hand, group_len):
            return possible_values_play(new_hand, group_len)
    
    # if curr_phase is phase 2, check whether the phase is playable
    if curr_phase == PHASE_TWO:
        possible_play2 = possible_phase_two(hand)
        if possible_play2:
            return possible_play2
    
    # if curr_phase is phase 3, check whether phase 3 is playable
    if curr_phase == PHASE_THREE:
        possible_play3 = possible_phase_three(hand)
        if possible_play3:
            return possible_play3
    
    # if curr_phase is phase 4, check whether it is playable
    if curr_phase == PHASE_FOUR:
        new_hand = groupby_values(hand)
        group_len = 4  # length of a group of cards in phase 4
        if possible_values_play(new_hand, group_len):
            return possible_values_play(new_hand, group_len)
    
    # if curr_phase is phase 5, check whether it is playable
    if curr_phase == PHASE_FIVE:
        run_len = 8  # run of 8 cards
        if possible_run(hand, run_len):
            return possible_run(hand, run_len)
    
    # if curr_phase is phase 6, check whether it is playable
    if curr_phase == PHASE_SIX:
        if possible_phase_six(hand):
            return possible_phase_six(hand)
        
    # if curr_phase is phase 7, check whether it is playable
    if curr_phase == PHASE_SEVEN:
        if possible_phase_seven(hand):
            return possible_phase_seven(hand)
    return False


def possible_values_play(new_hand, group_len):
    '''Takes a hand of cards, and returns a possible play for 2 sets of cards
    of the same values, where the number of cards in each set is determined
    by `group_len`. 
    Returns False if there are no possible plays'''
    # first check that the least number of cards is reached
    play_len = group_len * 2
    if len(new_hand) < play_len:
        return False
    
    # want combinations of length `play_len`, so that the cards can be split 
    # into 2 sets of cards of length `group_len`
    for combination in combinations(new_hand, play_len):
        comb_list = list(combination)
        first_group = []
        second_group = []
        new_hand_copy = new_hand.copy()
        # within the `play_len` number of cards, first find a set of cards of 
        # the same value with length `group_len`
        for first_comb in combinations(comb_list, group_len):
            set_1 = list(first_comb)
            if same_value(set_1) and num_natural(set_1) >= MIN_NATURAL:
                for card in set_1:
                    first_group.append(card)
                    new_hand_copy.remove(card)
                break
        # check if the remaining cards can form a set of cards of same value
        if first_group:
            for second_comb in combinations(new_hand_copy, group_len):
                set_2 = list(second_comb)
                if same_value(set_2) and num_natural(set_2) >= MIN_NATURAL:
                    for card in set_2:
                        second_group.append(card)
                    return [first_group, second_group]
    return False


def groupby_values(hand):
    '''Groups the cards in the hand by their values, and returns a new list
    that contains only the cards that have duplicates in the hand. as well
    as Aces. This will lower the computational time for the other functions'''
    grouped = groupby(sorted(hand), lambda x: x[0])
    new_hand = []
    for value, cards in grouped:
        card_list = list(cards)
        num_cards = len(card_list)
        if value == 'A' or num_cards >= 2:
            new_hand += card_list
    # return a reverse sorted hand here, as we want to play cards with higher 
    # values to minimise point gain
    return sorted(new_hand, reverse=True) 


def possible_phase_two(hand):
    '''Takes a hand of cards, and returns a possible play for phase 2.
    If there is no possible play, return False.'''
    freq_dict = dd(int)
    wilds = 0
    # Aces are not counted in the freq_dict, as they stand for all suits
    for card in hand:
        if card[0] != 'A':
            freq_dict[card[1]] += 1
        else:
            wilds += 1

    # Check if phase 2 is playable
    most_frequent_suit = max(freq_dict, key=lambda x: freq_dict[x])
    possible_play = []
    if freq_dict[most_frequent_suit] + wilds >= 7:
        for card in hand:
            # prioritise playing non ace cards first
            if (card[1] == most_frequent_suit and card[0] != 'A' 
                and len(possible_play) < 7):
                possible_play.append(card)
        for card in hand:
            if card[0] == 'A' and len(possible_play) < 7:
                possible_play.append(card)
        if num_natural(possible_play) >= MIN_NATURAL:
            return [possible_play]
    return False


def possible_phase_three(hand):
    '''Takes a hand of cards and returns a possible play for phase 3. 
    Returns False if it is not possible.'''
    # We want to play as many cards as possible with an accumulation, so start
    # searching for a combination of high number of cards that make up 34, if
    # this is not found, then move down to combinations of lower numbers of
    # cards.
    for i in range(len(hand), 0, -1):
        new_hand = hand.copy()
        first_accum = []
        second_accum = []
        if possible_accum(hand, i, ACCUM_34):
            first_accum = possible_accum(hand, i, ACCUM_34)
            for card in first_accum:
                new_hand.remove(card)
        # if first_accum has been found, repeat the same process, but with
        # new_hand, where the combination found has been removed from hand
        if first_accum:
            for i2 in range(len(new_hand), 0, -1):
                if possible_accum(new_hand, i2, ACCUM_34):
                    second_accum = possible_accum(new_hand, i2, ACCUM_34)
                    return [first_accum, second_accum]
    
    # No combinations were found, return False    
    return False


def possible_accum(hand, i, num):
    '''Determines whether the cards in `hand` are able to form an accumulation,
    where the sum of accumulation is determined by `num`. i indicates the 
    number of cards that should make up this sum. Returns the list of cards
    that make up the accumulation. 
    Returns False if it is not possible.'''
    accum = []
    for combination in combinations(hand, i):
        comb_list = list(combination)
        card_sum = sum(CARD_VALUES[x[0]] for x in comb_list)
        if card_sum == num:
            for card in comb_list:
                accum.append(card)
            return accum
    return False


def possible_run(hand, run_len):
    '''Take a hand, and returns a possible play for a run, where the length of
    the run is indicated by `run_len`.
    Returns False if there is no possible run.'''
    new_hand = []
    value_list = []
    wilds_list = []
    # Remove duplicates of the same value, and sort the list of cards in terms
    # of their value. also create a list of ACES if they exist
    for card in hand:
        if card[0] == 'A':
            wilds_list.append(card)
        elif card[0] not in value_list:    
            new_hand.append(card)
            value_list.append(card[0])
    sorted_hand = sorted(new_hand, key=lambda x: CARD_VALUES[x[0]])
    hand_copy = sorted_hand.copy()
    ace_copy = wilds_list.copy()

    # Pick a starting point in hand_copy, each time, hand_copy will cycle, in
    # that the first card becomes the last card. The starting point is reset
    for start_pt in range(len(sorted_hand)):
        if start_pt > 0:
            hand_copy.append(hand_copy.pop(0))
        ace_list = wilds_list.copy()
        num_wilds = len(ace_list)
        possible_run = hand_copy.copy()
        possible_run2 = hand_copy.copy()
        prev_card = hand_copy[0]
      
        # For each starting point, see if a run can be achieved by adding 
        # ACES to where there are values missing. Each time an ACE is added,
        # the same ACE is also taken away from ACE_list
        for i in range(1, len(hand_copy)):        
            card_x = hand_copy[i]
            value_diff = CARD_VALUES[card_x[0]] - CARD_VALUES[prev_card[0]]
                    
            # Consider the value_diff when the cards in the list cycles around,
            # the value_diff will be negative between specific cards
            if value_diff < 0:
                value_diff = MAX_RUN + value_diff
            if value_diff > 1:
                wilds_needed = value_diff - 1
                for num in range(wilds_needed):
                    if ace_list:
                        index = possible_run.index(card_x)
                        possible_run.insert(index, ace_list.pop())
                        num_wilds -= 1
            prev_card = card_x  
            # Check if the first sequence of cards of possible_run is a run
            if (len(possible_run) >= run_len and run(possible_run[:run_len]) 
                and num_natural(possible_run[:run_len]) >= MIN_NATURAL):
                return [possible_run[:run_len]]  
            
            # Consider the special case of when the iteration reaches the last
            # card in the original sorted hand. A run may still be achieved by
            # adding ACES to the end.
            if i == len(hand_copy) - 1 and hand_copy == sorted_hand:
                for ace in range(len(ace_copy)):
                    possible_run2.append(ace_copy.pop())
                if (len(possible_run2) >= run_len 
                    and run(possible_run2[:run_len])
                    and num_natural(possible_run2[:run_len]) >= MIN_NATURAL):
                    return [possible_run2[:run_len]]
    return False


def possible_phase_six(hand):
    '''Takes a hand, and returns a possible play for phase 6. 
    If it is not possible, return False.'''
    # first, create a dictionary mapping each color to a list of cards of the 
    # same color in the hand
    color_dict = dd(list)
    for card in hand:
        if card[1] in BLACK:
            color_dict[BLACK].append(card)
        else:
            color_dict[RED].append(card)
    
    # Just like in phase 3, we want to play as many cards as possible. 
    # Search for a combination of high number of cards that make up 34, if
    # this is not found, then try combinations of lower numbers of cards.
    first_accum = []
    second_accum = []
    
    # See if there is one set of accumulations from one color, and another set
    # of accumulations from a different color
    black_cards = color_dict[BLACK]
    for j in range(len(black_cards), 0, -1):
        if possible_accum(black_cards, j, ACCUM_34):
            first_accum = possible_accum(black_cards, j, ACCUM_34)
    red_cards = color_dict[RED]
    for k in range(len(red_cards), 0, -1):
        if possible_accum(red_cards, k, ACCUM_34):
            second_accum = possible_accum(red_cards, k, ACCUM_34)
    if first_accum and second_accum:
        return [first_accum, second_accum]
   
    first_accum = []
    second_accum = []
    # See if either of the colors can make up 2 sets of accumulations, just 
    # like testing for phase 3
    for color in color_dict:
        cards = color_dict[color]
        if possible_phase_three(cards):
            return possible_phase_three(cards)
    return False


def possible_phase_seven(hand):
    '''Takes a hand of cards, and returns a possible play for phase 7.
    Returns False if there are no possible plays'''
    # Approach this is a similar manner to the function `possible_values_play`
    # First check that the least number of cards is reached (8 cards)
    phase7_len = 8  
    if len(hand) < phase7_len:
        return False
    
    # want combinations of length 8, so that the cards can be split 
    # into 2 sets of cards of length 4
    for combination in combinations(hand, 8):
        comb_list = list(combination)
        first_group = []  # first group is same values
        second_group = []  # second group is run
        hand_copy = hand.copy()
        # within the 8 cards, first find a set of four cards of the same value
        for first_comb in combinations(comb_list, 4):
            set_1 = list(first_comb)
            if same_value(set_1) and num_natural(set_1) >= MIN_NATURAL:
                for card in set_1:
                    first_group.append(card)
                    hand_copy.remove(card)
                break
        # check if the remaining cards can form a run of 4 cards of same color
        if first_group:
            for second_comb in combinations(hand_copy, 4):
                set_2 = list(second_comb)
                if (same_color(set_2) and run(set_2) and 
                    num_natural(set_2) >= MIN_NATURAL):
                    for card in set_2:
                        second_group.append(card)
                    return [second_group, first_group]
    return False


if __name__ == '__main__':
    # Example call to the function.
    print(phazed_play(1, [(None, []), (4, [['2C', '3H', '4D', 'AD', '6S', '7C',
      '8S', '9H', '0S', 'JS']]), (None, []), (None, [])], [(0, [(2, 'JS'),
      (5, 'JS')]), (1, [(2, 'JS'), (3, (4, [['2C', '3H', '4D', 'AD', '6S',
      '7C', '8S', '9H']])), (4, ('0S', (1, 0, 8))), (4, ('JS',
      (1, 0, 9)))])], [0, 4, 0, 0], ['5D'], '7H'))