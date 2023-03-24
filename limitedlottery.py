import smartpy as sp

class Lottery(sp.Contract):
    def __init__(self):
        # storage - member variables
        self.init(
            participants = sp.map(l = {}, tkey=sp.TNat, tvalue=sp.TAddress),
            ticket_cost = sp.tez(1),
            tickets_avbl = sp.nat(5),
            max_tickets = sp.nat(5),
            max_tickets_per_address = sp.nat(2),

            # remove authorization
            #admin = sp.test_account("admin").address
        )

    @sp.entry_point
    def buy_ticket(self, numtickets):
        sp.set_type(numtickets, sp.TNat)

        #asserts
        sp.verify(self.data.tickets_avbl > 0, "NO TICKETS AVAILABLE.")
        sp.verify(
            sp.utils.mutez_to_nat(sp.amount) >= sp.utils.mutez_to_nat(self.data.ticket_cost) * numtickets, 
            "INSUFFICIENT BALANCE."
        )
        #post_total = numtickets + self.data.participants.values().count(sp.sender)
        post_total = sp.local("post_total", 0)
        post_total.value += numtickets
        sp.for item in self.data.participants.values():
            sp.if item == sp.sender:
                post_total.value += 1
        
        sp.verify(post_total.value <= self.data.max_tickets_per_address, "WILL EXCEED MAX TICKET LIMIT. (ADDRESS)")
        sp.verify(post_total.value <= self.data.max_tickets, "WILL EXCEED MAX TICKET LIMIT. (POOL)")
        
        #operations
        sp.for i in sp.range(0,numtickets,1):
            self.data.participants[sp.len(self.data.participants)] = sp.sender
            self.data.tickets_avbl = sp.as_nat(self.data.tickets_avbl - 1)

        change_amt = sp.utils.mutez_to_nat(sp.amount) - sp.utils.mutez_to_nat(self.data.ticket_cost) * numtickets#sp.amount - self.data.ticket_cost
        sp.if sp.utils.nat_to_mutez(sp.as_nat(change_amt)) > sp.tez(0):
            sp.send(sp.sender, sp.utils.nat_to_mutez(sp.as_nat(change_amt)))


    @sp.entry_point
    def end_lottery(self,random_seed):
        sp.set_type(random_seed, sp.TNat)

        #asserts
        sp.verify(self.data.tickets_avbl == 0, "UNUSED TICKETS IN STORAGE!")
        
        #remove authorization
        #sp.verify(sp.sender == self.data.admin, "UNAUTHORIZED ACTION.")

        #operations
        win_index = random_seed % self.data.max_tickets
        winner_address = self.data.participants[win_index]

        sp.send(winner_address, sp.balance)

        self.data.participants = {}
        self.data.tickets_avbl = self.data.max_tickets

    @sp.entry_point
    def reset_lottery(self):
        # TODO: return accumulated tezos in pool - nah
        self.data.participants = {}
        self.data.tickets_avbl = self.data.max_tickets
        
    
    @sp.entry_point
    def set_params(self, params):
        sp.set_type(params, sp.TRecord(ncost = sp.TMutez, nmax = sp.TNat, nmaxpadd = sp.TNat))

        #asserts
        sp.verify(self.data.tickets_avbl == self.data.max_tickets, "TRIED CHANGING VALUE DURING AN ONGOING GAME.")
        sp.verify(params.nmax >= params.nmaxpadd, "MAX NUMBER OF TICKETS MUST BE GREATER THAN MAX NUM OF TICKETS PER ADDRESS.")
        
        #remove authorization
        #sp.verify(sp.sender == self.data.admin, "UNAUTHORIZED ACCESS.")
        sp.verify(params.ncost > sp.tez(0), "INVALID PARAMETERS.")
        sp.verify(params.nmax > 0 , "INVALID PARAMETERS.")

        #operations
        self.data.ticket_cost = params.ncost
        self.data.max_tickets = params.nmax
        self.data.max_tickets_per_address = params.nmaxpadd
        self.data.tickets_avbl = params.nmax
        
        
        


@sp.add_test(name="main")
def test():
    scenario = sp.test_scenario()

    #Testing account
    bob = sp.test_account("bob")
    ali = sp.test_account("ali")
    admin = sp.test_account("admin")
    ccc = sp.test_account("ccc")
    ddd = sp.test_account("ddd")
    eee = sp.test_account("eee")
    fff = sp.test_account("fff")

    contract_1 = Lottery()

    scenario += contract_1

    scenario += contract_1.set_params(ncost = sp.tez(3), nmax = 10, nmaxpadd = 5).run(
        sender = admin, 
        now=sp.timestamp(1),
    )
    
    scenario += contract_1.buy_ticket(1).run(
        sender = admin, 
        now=sp.timestamp(1),
        amount = sp.tez(4),
    )

    scenario += contract_1.buy_ticket(1).run(
        sender = ali, 
        now=sp.timestamp(2),
        amount = sp.tez(3),
    )

    scenario += contract_1.buy_ticket(1).run(
        sender = admin, 
        now=sp.timestamp(3),
        amount = sp.tez(200),
    )

    scenario += contract_1.buy_ticket(2).run(
        sender = bob, 
        now=sp.timestamp(4),
        amount = sp.tez(237),
    )
    
    scenario += contract_1.buy_ticket(3).run(
        sender = ccc, 
        now=sp.timestamp(5),
        amount = sp.tez(15),
    )

    scenario += contract_1.buy_ticket(2).run(
        sender = admin, 
        now=sp.timestamp(6),
        amount = sp.tez(67),
    )

    scenario += contract_1.set_params(ncost = sp.tez(3), nmax = 10, nmaxpadd = 5).run(
        sender = admin, 
        now=sp.timestamp(1),
        valid = False
    )

    scenario += contract_1.end_lottery(26).run(
        now = sp.timestamp(7),
        sender = admin
    )

    scenario += contract_1.set_params(ncost = sp.tez(3), nmax = 10, nmaxpadd = 5).run(
        sender = admin, 
        now=sp.timestamp(1),
    )