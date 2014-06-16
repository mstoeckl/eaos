
class Node():
    def __init__(self, redo, onchange, dependencies=tuple()):
        self.redo = redo
        self.onchange = onchange
        self.dependencies = dependencies
        self.data = None
        self.futures = dict()

        for node in self.dependencies:
            node.futures[id(self)] = self
    def unlink(self):
        for node in self.dependencies:
            del node.futures[id(self)]
        self.dependencies = []
    def __del__(self):
        self.unlink()

    def __repr__(self):
        return "[N: {} -> {}]".format(self.redo.__name__, self.onchange.__name__)
    def __hash__(self):
        return id(self)
    def __eq__(self, o):
        return id(self) == id(o)

    @staticmethod
    def multi_update(kvp):
        """
        N objects are dirty and can be fed updates.  Feed them their updates and also resolve the network
        without unnecessary redos.
        """
        pass


    def update(self, input=None):
        dirty = dict()
        dirty[id(self)] = self
        while dirty:
            # grab a Node that is dirty but has no dirty dependencies
            node = next(iter(dirty.items()))[1]
            impure = True
            while impure:
                impure = False
                for dep in node.dependencies:
                    if id(dep) in dirty:
                        node = dep
                        impure = True
                        break

            # update
            del dirty[id(node)]
            if input != None and node == self:
                data = node.redo(input, *[dep.data for dep in node.dependencies])
            else:
                data = node.redo(*[dep.data for dep in node.dependencies])
            if data != node.data:
                node.data = data
                node.onchange(node.data)
                for i in node.futures:
                    dirty[i] = node.futures[i]









if __name__ == "__main__":
    # TODO class link():
    #      """ The lurking behemoth """
    #         ...

    # things I'd like to try

    @link()
    def schedule(this):
        return this

    @link(dim=1, dependencies=[schedule, (actions, link.dim(0)), (scores, link.dim(0))])
    def match(this, schedule, actions, scores):
        return this

    @link(dim=1, dependencies=[schedule, (match, link.vary())])
    def robot(this, schedule, *matches):
        # if the return value != previous value, all dependencies are dirtied
        return this

    @link(dim=1, dependencies=[(match, link.dim(0))])
    def page(this, match):

        return this

    @link(default=None) # which is the default "this" anyway.
    def saver(this):
        return this

    S = schedule()
    M = {}
    for x in range(16):
        M[x] = (match(x),link.make(actions,x),scores(x).make())
        # last one is no-op, since foink(x) creates it..
    link.delete(actions, 15)
    match(15).delete()
    link.delete(scores, 15)
    robot("13-x").vary_dependencies(match, [11,23,"33"])
    saver().add_dependency(match, link.all())
    saver().remove_dependency(match)
    saver().dirty() # triggers an update


    # if you really want to, redirect again:
    with Link() as link:
        with Link() as link2:
            @link2(default=11)
            def foo(this):
                return this
            foo().modify(13)
            link.recalculate()

    assert lambda *x:x[0] == link.dim(0)


