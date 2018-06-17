import bmesh
import itertools as it
from mathutils import Vector
from bmesh.types import BMVert, BMEdge

from ..util_rail import rails_types as rails
from ...utils import (
    split,
    select,
    split_quad,
    filter_geom,
    get_edit_mesh,
    face_with_verts,
    calc_edge_median,
    filter_vertical_edges,
    filter_horizontal_edges
    )

def make_stairs(bm, faces, step_count, step_width, landing, landing_width, stair_direction, railing, **kwargs):
    """Extrude steps from selected faces

    Args:
        step_count (int): Number of stair steps
        step_width (float): width of each stair step
        landing (bool): Whether the stairs have a landing
        landing_width (float): Width of the landing if any
        **kwargs: Extra kwargs from StairsProperty

    """

    for f in faces:
        f.select = False

        f = make_stair_split(bm, f, **kwargs)

        _key = lambda v:v.co.z
        fheight =  max(f.verts, key=_key).co.z - min(f.verts, key=_key).co.z

        # -- options for railing
        top_faces = []
        init_normal = f.normal.copy()

        ext_face = f
        for i in range(step_count):
            # extrude face
            n = ext_face.normal
            ext_width = landing_width if (landing and i==0) else step_width
            ret_face = bmesh.ops.extrude_discrete_faces(bm,
                faces=[ext_face]).get('faces')[-1]

            bmesh.ops.translate(bm, vec=n * ext_width,
                verts=ret_face.verts)

            # -- keep reference to top faces for railing
            top_faces.append(list({f for e in ret_face.edges for f in e.link_faces
                                if f.normal.z > 0})[-1])

            if landing and i == 0:
                # adjust ret_face based on stair direction

                left_normal, right_normal = (
                        ret_face.normal.cross(Vector((0, 0, 1))),
                        ret_face.normal.cross(Vector((0, 0, -1))),
                    )
                left = list({f for e in ret_face.edges for f in e.link_faces
                                    if f.normal.to_tuple(4) == left_normal.to_tuple(4)})[-1]
                right = list({f for e in ret_face.edges for f in e.link_faces
                                    if f.normal.to_tuple(4) == right_normal.to_tuple(4)})[-1]

                # set appropriate face for next extrusion
                if stair_direction == 'FRONT':
                    pass
                elif stair_direction == 'LEFT':
                    ret_face = left
                elif stair_direction == 'RIGHT':
                    ret_face = right

            if i < (step_count-1):
                # cut step height
                res = split_quad(bm, ret_face, False, 1)
                bmesh.ops.translate(bm,
                    verts=filter_geom(res['geom_inner'], BMVert),
                    vec=(0, 0, (fheight/2)-(fheight/(step_count-i))))

                # update ext_face
                ext_face = min([f for f in filter_geom(res['geom_inner'], BMVert)[-1].link_faces],
                    key=lambda f: f.calc_center_median().z)

    # if railing:
    #     make_stairs_railing(bm, init_normal, top_faces, landing, stair_direction, **kwargs)

def make_stair_split(bm, face, size, off, **kwargs):
    """Use properties from SplitOffset to subdivide face into regular quads

    Args:
        bm   (bmesh.types.BMesh):  bmesh for current edit mesh
        face (bmesh.types.BMFace): face to make split (must be quad)
        size (vector2): proportion of the new face to old face
        off  (vector3): how much to offset new face from center
        **kwargs: Extra kwargs from WindowProperty

    Returns:
        bmesh.types.BMFace: New face created after split
    """
    return split(bm, face, size.y, size.x, off.x, off.y, off.z)


def make_stairs_railing(bm, normal, faces, has_landing, stair_direction, **kwargs):
    """Create railing for stairs

    Args:
        normal (Vector3): Normal direction for initial face of stairs
        faces (list): top faces of the stairs
        has_landing (bool): whether the stairs have landing
        stair_direction (Enum): Direction of stairs, if has_landing is true
        **kwargs: Extra properties from StairsPropertyGroup
    """

    # -- create railing for landing
    if has_landing:
        landing_face, *step_faces = faces

        if stair_direction == 'FRONT':
            make_railing_front(bm, landing_face, normal, **kwargs)
        elif stair_direction == 'LEFT':
            make_railing_left(bm, landing_face, normal, **kwargs)
        elif stair_direction == 'RIGHT':
            make_railing_right(bm, landing_face, normal, **kwargs)

    else:
        step_faces = faces

    # --create railing for steps
    make_step_railing(step_faces, has_landing, stair_direction)

def make_railing_front(bm, face, normal, **kwargs):
    """Create rails for landing when stair direction is front

    Args:
        bm (bmesh.types.BMesh): bmesh of current edit object
        face (bmesh.types.BMFace): Top face of the landing
        normal (Vector3): Normal direction for the initial face of stairs
        **kwargs: Description
    """

    # -- determine left and right edges, based on normal
    valid_edges = []
    ref = face.calc_center_median()
    for e in face.edges:
        diff = ref - calc_edge_median(e)
        if diff * Vector(map(abs, normal.to_tuple(1))) == 0: # MAGIC!!
            valid_edges.append(e)

    # -- add railing on edges
    rails.make_railing(bm, valid_edges, **kwargs)

def make_railing_left(bm, face, normal, **kwargs):
    """Create rails for landing when stair direction is left

    Args:
        bm (bmesh.types.BMesh): bmesh of current edit object
        face (bmesh.types.BMFace): Top face of the landing
        normal (Vector3): Normal direction for the initial face of stairs
        **kwargs: Description
    """

    # -- determine front and right edges, based on normal
    pass

def make_railing_right(face, normal):
    pass

def make_step_railing(faces, landing, direction):
    pass
