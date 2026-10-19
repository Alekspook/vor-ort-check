"""Erzeugt vereinfachte 3D-Modelle (USDZ, AR Quick Look) des EcoFlow OCEAN 2 in Originalgröße:
Wechselrichter 680 x 406,5 x 203 mm (B x H x T), darunter 1–3 Batterien 680 x 279 x 196 mm.
Maße laut energy.ecoflow.com/uk/products/ocean-2-home-battery. Aufruf mit usd-core:
  python make_ocean2_usdz.py <ausgabeordner>"""
import sys, os
from pxr import Usd, UsdGeom, UsdShade, UsdUtils, Sdf, Gf

out_dir = sys.argv[1]
os.makedirs(out_dir, exist_ok=True)
W, INV_H, INV_D, BAT_H, BAT_D, GAP = 0.680, 0.4065, 0.203, 0.279, 0.196, 0.008

def material(stage, path, rgb, rough=0.55, emissive=None):
    mat = UsdShade.Material.Define(stage, path)
    sh = UsdShade.Shader.Define(stage, path + "/Surface")
    sh.CreateIdAttr("UsdPreviewSurface")
    sh.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*rgb))
    sh.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(rough)
    sh.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.0)
    if emissive:
        sh.CreateInput("emissiveColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*emissive))
    mat.CreateSurfaceOutput().ConnectToSource(sh.ConnectableAPI(), "surface")
    return mat

def box(stage, path, cx, cy, cz, sx, sy, sz, mat):
    cube = UsdGeom.Cube.Define(stage, path)
    cube.CreateSizeAttr(1.0)
    x = UsdGeom.XformCommonAPI(cube)
    x.SetTranslate(Gf.Vec3d(cx, cy, cz))
    x.SetScale(Gf.Vec3f(sx, sy, sz))
    UsdShade.MaterialBindingAPI.Apply(cube.GetPrim()).Bind(mat)

def build(n_bat):
    name = f"ocean2-{n_bat}"
    usda = os.path.join(out_dir, name + ".usdc")
    stage = Usd.Stage.CreateNew(usda)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    root = UsdGeom.Xform.Define(stage, "/Ocean2")
    stage.SetDefaultPrim(root.GetPrim())
    prim = root.GetPrim()
    # AR Quick Look: an senkrechter Fläche (Wand) verankern
    prim.CreateAttribute("preliminary:anchoring:type", Sdf.ValueTypeNames.Token).Set("plane")
    prim.CreateAttribute("preliminary:planeAnchoring:alignment", Sdf.ValueTypeNames.Token).Set("vertical")

    body = material(stage, "/Ocean2/Looks/Body", (0.80, 0.82, 0.83), 0.6)
    front = material(stage, "/Ocean2/Looks/Front", (0.93, 0.94, 0.94), 0.45)
    dark = material(stage, "/Ocean2/Looks/Dark", (0.12, 0.13, 0.14), 0.7)
    light = material(stage, "/Ocean2/Looks/Light", (0.85, 0.95, 1.0), 0.3, emissive=(0.55, 0.8, 1.0))

    total_h = INV_H + n_bat * (BAT_H + GAP)
    y = total_h / 2.0   # Ursprung in der Mitte: das Gerät erscheint mittig, wo man tippt
    # Wechselrichter oben
    top = y; cy = top - INV_H / 2
    box(stage, "/Ocean2/Inverter", 0, cy, INV_D / 2, W, INV_H, INV_D, body)
    box(stage, "/Ocean2/InverterFront", 0, cy, INV_D + 0.001, W - 0.02, INV_H - 0.02, 0.002, front)
    box(stage, "/Ocean2/InverterLight", 0, cy - INV_H * 0.25, INV_D + 0.0025, W * 0.42, 0.006, 0.002, light)
    y = top - INV_H
    for i in range(n_bat):
        y -= GAP
        box(stage, f"/Ocean2/Gap{i}", 0, y + GAP / 2, BAT_D / 2, W - 0.03, GAP, BAT_D - 0.02, dark)
        cy = y - BAT_H / 2
        box(stage, f"/Ocean2/Battery{i}", 0, cy, BAT_D / 2, W, BAT_H, BAT_D, body)
        box(stage, f"/Ocean2/BatteryFront{i}", 0, cy, BAT_D + 0.001, W - 0.02, BAT_H - 0.02, 0.002, front)
        box(stage, f"/Ocean2/BatteryLed{i}", W / 2 - 0.06, cy + BAT_H / 2 - 0.035, BAT_D + 0.0025, 0.03, 0.004, 0.002, light)
        y -= BAT_H
    stage.GetRootLayer().Save()
    usdz = os.path.join(out_dir, name + ".usdz")
    ok = UsdUtils.CreateNewARKitUsdzPackage(Sdf.AssetPath(usda), usdz)
    os.remove(usda)
    print(name, "ok" if ok else "FEHLER", round(total_h * 1000), "mm hoch", os.path.getsize(usdz), "bytes")

for n in (1, 2, 3):
    build(n)
