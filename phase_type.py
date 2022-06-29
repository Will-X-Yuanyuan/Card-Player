# Contains functions that deal with the type of play (phase) allowed

def phazed_phase_type(phase):
    '''Takes a 'phase' and returns a sorted list of corresponding phase numbers 
    Returns an empty list if there are no valid phase combinations.'''
    num_groups = len(phase)
    phase_list = []
    
    # Check if the phase is 1
    if num_groups == 2:
        # check that both sets of cards include 3 cards, and at least 2 natural
        if (len(phase[0]) == 3 and num_natural(phase[0]) >= MIN_NATURAL and 
            len(phase[1]) == 3 and num_natural(phase[1]) >= MIN_NATURAL):
            if same_value(phase[0]) and same_value(phase[1]):
                phase_list.append(PHASE_ONE)   
            
    # Check if the phase is 2 (All cards have equal suits)
    if num_groups == 1:
        num_cards = len(phase[0])
        group = phase[0]
        if num_cards == 7 and num_natural(group) >= MIN_NATURAL:
            same_suit = True
            
            # Set a test case for the suit, this test case cannot be wild
            for value, suit in group:
                if value == 'A':
                    continue
                test_suit = suit
        
            for value, suit in group:
                if value != 'A' and suit != test_suit:
                    same_suit = False
                    break
            if same_suit:
                phase_list.append(PHASE_TWO)
        
    # Check if the phase is 3
    if num_groups == 2:
        if accumulation(phase[0]) and accumulation(phase[1]):
            phase_list.append(PHASE_THREE)
    
    # Check if the phase is 4
    if num_groups == 2:
        # Check if both groups include 4 cards, and at least 2 natural cards
        if (len(phase[0]) == 4 and num_natural(phase[0]) >= MIN_NATURAL and 
            len(phase[1]) == 4 and num_natural(phase[1]) >= MIN_NATURAL):
            if same_value(phase[0]) and same_value(phase[1]):
                phase_list.append(PHASE_FOUR)
    
    # Check if the phase is 5
    if num_groups == 1:
        group = phase[0]
        if len(group) == 8 and num_natural(group) >= MIN_NATURAL:
            if run(group):
                phase_list.append(PHASE_FIVE)
    
    # Check if the phase is 6
    if num_groups == 2:
        if (accumulation(phase[0]) and same_color(phase[0]) and 
            accumulation(phase[1]) and same_color(phase[1])):
            phase_list.append(PHASE_SIX)
        
    # Check if the phase is 7
    if num_groups == 2:
        
        # Check that the first group is a run of 4 cards of the same color
        if (len(phase[0]) == 4 and num_natural(phase[0]) >= MIN_NATURAL and 
            run(phase[0]) and same_color(phase[0])):
            
            # Then check if the second group is 4 cards of the same value
            if (len(phase[1]) == 4 and num_natural(phase[1]) and 
                same_value(phase[1])):
                phase_list.append(PHASE_SEVEN)
    
    return sorted(phase_list)

def num_natural(group):
    '''Returns the number of wild cards in any set of cards'''
    num = 0
    for card in group:
        if card[0] != 'A':
            num += 1
    return num


def same_value(group):
    '''checks whether the cards have the same value. 
    Return True if yes. False otherwise.'''
    same_value = True
        
    # set a test value, but this test value cannot be Ace
    test_value = ''
    for card in group:
        if card[0] != 'A':
            test_value = card[0]
            break
    
    for card in group:
        if card[0] != 'A' and card[0]!= test_value:
            same_value = False
    return same_value


def run(group):
    '''Checks whether the cards are a run. 
    Returns True if yes. False otherwise'''
    # Check that the run is no longer than 12 cards
    if len(group) > MAX_RUN:
        return False
    
    # two cycles of 2 to K will encompass all possible runs (excluding wilds)
    run_test = "234567890JQK234567890JQK" 
    
    run_list = [card[0] for card in group]
    # Get rid of any consecutive wild cards at the beginning of the run_list
    while run_list[0] == 'A':
        run_list.remove('A')
        
    # Knowing that the first element is not a wild card, we can replace all 
    # remaining wild cards with a new card value that is 1 larger than the 
    # previous card value
    previous_value = run_list[0]
    for i in range(len(run_list)):
        value = run_list[i]
        if value == 'A':
            value_list = list("234567890JQK2")
            prev_index = value_list.index(previous_value)
            value = value_list[prev_index + 1]
            run_list[i] = value
        previous_value = value         
    
    # Then, compare the altered list with the run_test to see if it's a run
    altered_run_list = ''.join(run_list)
    if altered_run_list in run_test:
        return True
    return False


def same_color(group):
    '''Checks if the cards are of the same color. Returns True if yes. 
    False otherwise'''
    
    # Pick a color to be the test color, then compare all cards to this test
    # case, but this test color cannot come from a wild card. 
    test_color = ''
    for card in group:
        if card[0] != 'A' and card[1] in RED:
            test_color = RED
            break
        elif card[0] != 'A' and card[1] in BLACK:
            test_color = BLACK
            break
    
    for card in group:
        if card[0] != 'A' and card[1] not in test_color:
            return False
    return True


def accumulation(group):
    '''Checks whether the group of cards is an accumulation of 34. 
    Returns True if yes, False if not.'''
    
    card_sum = sum(CARD_VALUES[card[0]] for card in group)
    if card_sum == 34:
        return True
    return False

def same_suit(group):
    '''Takes a group and checks whether the cards have the same suit.
    Returns True if yes, False otherwise.'''
    # Set a test case for the suit, this test case cannot be wild
    for value, suit in group:
        if value == 'A':
            continue
        test_suit = suit
    
    for value, suit in group:
        if value != 'A' and suit != test_suit:
            return False
    return True