# Optimisation Variables

`x[service, period, room]` is a continuous allocation variable for forecast planning-demand hours assigned to an
eligible room.

`y[room]` is a binary room-active variable. Protected rooms are fixed active by constraint.

`z[building]` is a binary building-active variable. A building can be marked potentially releasable in the mathematical
candidate only when all rooms are inactive and no allocation remains.

`m[service, source_site, target_site]` is a binary move variable used when site movement is allowed.

`u[service, period]` is unmet-demand slack. It carries a prohibitive penalty and a case with material unmet demand is
not presented as an ordinary feasible result.

`r[service, period]` is optional remote demand, bounded by configured remote-eligible limits and face-to-face floors.
