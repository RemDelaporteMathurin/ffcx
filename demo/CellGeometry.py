# Copyright (C) 2013 Martin S. Alnaes
#
# A functional M involving a bunch of cell geometry quantities.
import basix.ufl
from ufl import (CellVolume, Circumradius, Coefficient, FacetArea, FacetNormal,
                 SpatialCoordinate, ds, dx, tetrahedron)

cell = tetrahedron
V = basix.ufl.element("P", cell.cellname(), 1)
u = Coefficient(V)

# TODO: Add all geometry for all cell types to this and other demo files, need for regression test.
x = SpatialCoordinate(cell)
n = FacetNormal(cell)
vol = CellVolume(cell)
rad = Circumradius(cell)
area = FacetArea(cell)

M = u * (x[0] * vol * rad) * dx + u * (x[0] * vol * rad * area) * ds  # + u*area*avg(n[0]*x[0]*vol*rad)*dS
