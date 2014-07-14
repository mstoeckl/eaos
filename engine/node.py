from copy import deepcopy


class sentinel():

    def __init__(self, desc):
        self.__name__ = desc

    def __call__(self, *a, **k):
        return self

    def __repr__(self):
        return "<sentinel:{}>".format(self.__name__)


class link():

    """ The lurking behemoth """

    def __init__(self, default=None, dim=0, dependencies={}):
        if not isinstance(dim, int) or dim < 0:
            e = Exception("\"dim\" argument should be non-negative integer")
            raise e

        if not isinstance(dependencies, dict):
            e = Exception(
                "Dependency must be a dictionary of proxy-sentinel pairs. Bad dog.")
            raise e

        for proxy, rule in dependencies.items():
            if not isinstance(proxy, link._proxy):
                e = Exception(
                    "Rule {} ought to have a proxy key.".format({proxy: rule}))
                raise e
            if not isinstance(rule, sentinel):
                e = Exception(
                    "Rule '{}' ought to end with a sentinel value.".format({proxy: rule}))
                raise e

        self.kwargs = {
            "default": default,
            "dim": int(dim),
            "dependencies": dict(dependencies)}

    def __call__(self, func):
        """
        Returns a reference-object from a function
        """
        name = func.__name__
        if name == "<lambda>":
            e = Exception("No anonymous functions here, boy. Get out!")
            raise e
        if name in link._table:
            e = Exception(
                "Oh no! You've got two functions with the same name, \"{}\"".format(name))
            raise e

        return link._proxy(func, **self.kwargs)

    """
    Table from which one can look up

    """
    _table = {}
    """
    The dirty table. Contains type=set-of-instances pairs
    """
    _dirty = {}
    """
    Type based class-selectors capture all class-elements.
    """
    _typehooks = {}
    """
    Type lookup.
    """
    _types = {}
    """
    Order of resolution for types, with the low-level nodes
    first.
    """
    _resolution_order = []

    class _proxy():

        """
        This object takes the place of the original function.

        """

        def __init__(self, func, **kwargs):
            self.func = func
            name = func.__name__

            self.default = kwargs["default"]
            self.dim = kwargs["dim"]
            self.deps = kwargs["dependencies"]

            # vector subtable
            link._table[name] = {}
            link._typehooks[name] = set()
            link._types[name] = self
            link._resolution_order.append(self)
            link._dirty[name] = set()

        #def __hash__(self):
            #return id(self)

        def __repr__(self):
            return "<proxy:{}>".format(self.func.__name__)

        def __call__(self, *vector):
            """ Calling this returns a proxy object...
                The arguments are the spacial ID of the object, and must be hashable.
                """

            vector = tuple(vector)
            if len(vector) != self.dim:
                e = Exception(
                    "Ya claimed '{}' took a vector id of dimension {}. But you gave it {}!".format(
                        self.func.__name__,
                        self.dim,
                        vector))
                raise e
            try:
                hash(vector)
            except TypeError:
                e = Exception(
                    "Every vector ID must be hashable. We can't trust your '{}'.".format(vector))
                raise e

            if self.func.__name__ in link._table:
                branch = link._table[self.func.__name__]
                if vector in branch:
                    return branch[vector]

            for proxy, rule in self.deps.items():
                if rule == link.only and proxy.dim != 0:
                    e = Exception(
                        "Selector '{}' needs a dim=0 matching proxy. Does it? NO!".format(
                            link.match))
                    raise e

                if rule in (link.only, link.match):
                    v = {link.match: vector, link.only: ()}[rule]

                    if v not in link._table[proxy.func.__name__]:
                        e = Exception(
                            "Selector 'link.match' requires that the matched dependency ({} -> {}) exists. Guess what went wrong.".format(
                                proxy.func.__name__,
                                vector))
                        raise e

            node = link._instance(
                self.func,
                self,
                vector,
                self.default,
                self.deps)
            link._table[self.func.__name__][vector] = node

            return node

    class _instance():

        """
        This is an individual function-stage-object with state.
        Woo!
        """

        def __init__(self, func, type, vector, default, deps):
            self.state = default
            self.func = func
            self.vector = vector
            self.downstream = set()

            # handle deps
            self.varies = {}
            self.deps = deps
            for proxy, rule in self.deps.items():
                name = proxy.func.__name__

                if rule == link.vary:
                    self.varies[proxy] = {}
                elif rule in (link.match, link.only):
                    v = {link.match: vector, link.only: ()}[rule]
                    elem = link._table[name][v]
                    elem.downstream.add(self)
                elif rule == link.all:
                    link._typehooks[name].add(self)
                else:
                    e = Exception(
                        "Rule class {} not identified. Oops.".format(rule))
                    raise e

        def __hash__(self):
            return id(self)

        def __repr__(self):
            return "<X-{} {}>".format(self.func.__name__, self.vector)

        def dirty(self):
            """
            Mark instance as unclean; get ready to be updated! :-)

            Returns self for chaining.
            """
            link._dirty[self.func.__name__].add(self)
            return self

        in_place = sentinel("in_place")

        def modify(self, new_state=in_place):
            """
            Sets state.
            All dependent nodes are marked dirty.

            Returns self for chaining.
            """
            if new_state is not link._instance.in_place:
                self.state = new_state
            for element in self.get_downstream_dependencies():
                link._dirty[element.func.__name__].add(element)

            return self

        def __call__(self, **dependency_data):
            """
            Return true if state changed; else return false.
            Careful: State is copied to permit safe modifications
            """
            next_state = self.func(
                self.vector, deepcopy(self.state), **dependency_data)
            if next_state != self.state:
                self.state = next_state
                return True

            return False

        def get_upstream_data(self):
            """ Return class/link based upstream data in dict or single format """
            data = {}
            for proxy, rule in self.deps.items():
                name = proxy.func.__name__
                if rule == link.vary:
                    d = {}
                    for vector, item in self.varies[proxy].items():
                        d[vector] = item.state
                    data[name] = d
                elif rule in (link.match, link.only):
                    v = {link.match: self.vector, link.only: ()}[rule]
                    data[name] = link._table[name][v].state
                elif rule == link.all:
                    d = {}
                    for item in link._table[name].values():
                        d[item.vector] = item.state
                    data[name] = d
                else:
                    e = Exception("Alas, Rule class {} unknown.".format(rule))
                    raise e

            return data

        def get_upstream_dependencies(self):
            """ Return class/link based upstreams """
            elems = set()
            for proxy, rule in self.deps.items():
                name = proxy.func.__name__
                if rule == link.vary:
                    for item in self.varies[proxy].values():
                        elems.add(item)
                elif rule in (link.match, link.only):
                    v = {link.match: self.vector, link.only: ()}[rule]
                    elems.add(link._table[name][v])
                elif rule == link.all:
                    for item in link._table[name].values():
                        elems.add(item)
                else:
                    e = Exception("Alas, Rule class {} unknown.".format(rule))
                    raise e

            return elems

        def get_downstream_dependencies(self):
            g = set()
            for cont in self.downstream:
                g.add(cont)
            for cont in link._typehooks[self.func.__name__]:
                g.add(cont)
            return g

        def delete(self):
            """
            Unlink an element. Goodbye, world.
            """
            if self.downstream:
                e = Exception(
                    "Poor fool. Unlinking an object before its dependencies are ready.")
                raise e

            del link._table[self.func.__name__][self.vector]

            for proxy, rule in self.deps.items():
                name = proxy.func.__name__

                if rule == link.vary:
                    for item in self.varies[proxy].values():
                        item.downstream.remove(self)
                elif rule in (link.match, link.only):
                    v = {link.match: self.vector, link.only: ()}[rule]
                    elem = link._table[name][v]
                    elem.downstream.remove(self)
                elif rule == link.all:
                    link._typehooks[name].remove(self)
                else:
                    e = Exception(
                        "Rule class {} mysterious. Oh noes!".format(rule))
                    raise e

        def wipe(self, proxy):
            """

            """
            if proxy not in self.varies:
                e = Exception(
                    "Proxy {} has gotta be a rule dependency of type {}.".format(
                        proxy,
                        link.vary))
                raise e

            # continue...
            for vector in list(self.varies[proxy].keys()):
                elem = self.varies[proxy].pop(vector)
                elem.downstream.remove(self)

            return self

        def _vary_clean(self, proxy, *ids):
            if proxy not in self.varies:
                e = Exception(
                    "Proxy {} must be part of dependencies with rule {}. Or else.".format(
                        proxy,
                        link.vary))
                raise e

            vectors = set(ids)
            for v in vectors:
                if not isinstance(v, tuple) or len(v) != proxy.dim:
                    e = Exception(
                        "Vector ID '{}' ain't matchin' proxy type.".format(v))
                    raise e
            return vectors

        def add(self, proxy, *ids):
            """
            Add the specified vector ids to a variable dependency
            """
            vectors = self._vary_clean(proxy, *ids)
            name = proxy.func.__name__
            for vector in vectors:
                d = link._table[name]
                if vector not in d:
                    e = Exception(
                        "Won't add element '{}' if it doesn't exist. Not I.".format(vector))
                    raise e

                elem = d[vector]
                self.varies[proxy][vector] = elem
                elem.downstream.add(self)

            return self

        def remove(self, proxy, *ids):
            """
            Remove the specified vector ids from a variable dependency
            """
            vectors = self._vary_clean(proxy, *ids)
            for vector in vectors & self.varies[proxy].keys():
                elem = self.varies[proxy].pop(vector)
                elem.downstream.remove(self)

            return self

    @staticmethod
    def clean():
        """
        Update all dirty nodes exactly once. Some downstream nodes
        get muddy in the process: let's update them too (once)! Once.
        Once. Once. Update.
        """
        # run the cleaning algorithm!
        for proxy in link._resolution_order:
            segment = link._dirty[proxy.func.__name__]
            while segment:
                node = segment.pop()
                if node(**node.get_upstream_data()):
                    for cont in node.get_downstream_dependencies():
                        link._dirty[cont.func.__name__].add(cont)

    @staticmethod
    def list(proxy_type):
        """
        Return a list of vector-ids for a given type
        """
        if not isinstance(proxy_type, link._proxy):
            e = Exception("Not a proxy type. Not at all.")
            raise e
        return set(link._table[proxy_type.func.__name__].keys())

    """
    sentinels to mark rules
    """
    vary = sentinel("vary")  # changable dependencies for a type
    match = sentinel("match")  # vector is the same
    only = sentinel("only")  # only element of dim=0 class
    all = sentinel("all")  # all elements of dim=0 class, report as dict

if __name__ == "__main__":

    @link(default=0)
    def woop(this):
        print("woop", this)
        return this + 1

    @link(dim=1, default=True, dependencies={woop: link.all})
    def bar(this, woop=0):
        print("bar", this, woop)
        return not this

    @link(dim=1, default=[1], dependencies={woop: link.only, bar: link.match})
    def foo(this, woop=0, bar=0):
        print("foo", this, woop, bar)
        if bar:
            return this
        else:
            return this * 2

    @link(dependencies={foo: link.vary})
    def variable(this, foo=0):
        print("variable", foo)
        pass

    woop()
    bar(1)
    bar(2)
    foo(1)
    foo(2)
    v = variable()
    v.wipe(foo)
    v.add(foo, (1,))
    v.add(foo, (2,))
    v.remove(foo, (1,))

    print(v.varies)

    for i in range(5):
        if i == 2:
            bar(2).dirty()
            link.clean()
        else:
            woop().dirty()
        link.clean()
        print()

    variable().delete()
    foo(2).delete()
    foo(1).delete()
    bar(2).delete()
    bar(1).delete()

    link.clean()
