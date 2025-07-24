import ezdxf
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import math
import argparse

def draw_entities(entities, ax):
    """Draw DXF entities on matplotlib axes"""
    for e in entities:
        try:
            if e.dxftype() == 'LINE':
                start, end = e.dxf.start, e.dxf.end
                ax.plot([start.x, end.x], [start.y, end.y], color='black', linewidth=0.5)

            elif e.dxftype() == 'CIRCLE':
                center, radius = e.dxf.center, e.dxf.radius
                circle = plt.Circle((center.x, center.y), radius, fill=False, color='black', linewidth=0.5)
                ax.add_patch(circle)

            elif e.dxftype() == 'ARC':
                center, radius = e.dxf.center, e.dxf.radius
                start_angle = math.radians(e.dxf.start_angle)
                end_angle = math.radians(e.dxf.end_angle)
                
                # Handle arcs that cross 0° (start_angle > end_angle)
                if e.dxf.start_angle > e.dxf.end_angle:
                    # Arc crosses 0°, need to go from start_angle to 2π, then from 0 to end_angle
                    theta1 = np.linspace(start_angle, 2 * math.pi, 50)
                    theta2 = np.linspace(0, end_angle, 50)
                    theta = np.concatenate([theta1, theta2])
                else:
                    # Normal arc
                    theta = np.linspace(start_angle, end_angle, 100)
                
                x = center.x + radius * np.cos(theta)
                y = center.y + radius * np.sin(theta)
                ax.plot(x, y, color='black', linewidth=0.5)

            elif e.dxftype() == 'LWPOLYLINE':
                points = e.get_points('xy')
                if len(points) > 1:
                    if e.closed:
                        points = list(points) + [points[0]]  # Close the polyline
                    x, y = zip(*points)
                    ax.plot(x, y, color='black', linewidth=0.5)

            elif e.dxftype() == 'POLYLINE':
                if not e.is_3d_polyline and not e.is_3d_mesh:
                    points = [v.dxf.location for v in e.vertices]
                    if len(points) > 1:
                        if e.is_closed:
                            points.append(points[0])  # Close the polyline
                        x = [p.x for p in points]
                        y = [p.y for p in points]
                        ax.plot(x, y, color='black', linewidth=0.5)

            elif e.dxftype() == 'ELLIPSE':
                # Basic ellipse support
                center = e.dxf.center
                major_axis = e.dxf.major_axis
                ratio = e.dxf.ratio
                start_param = e.dxf.start_param
                end_param = e.dxf.end_param
                
                # Create ellipse points
                if end_param < start_param:
                    end_param += 2 * math.pi
                t = np.linspace(start_param, end_param, 100)
                
                # Major and minor axis lengths
                major_length = math.sqrt(major_axis.x**2 + major_axis.y**2)
                minor_length = major_length * ratio
                
                # Rotation angle
                rotation = math.atan2(major_axis.y, major_axis.x)
                
                # Parametric ellipse
                x_local = major_length * np.cos(t)
                y_local = minor_length * np.sin(t)
                
                # Rotate and translate
                cos_rot = math.cos(rotation)
                sin_rot = math.sin(rotation)
                x = center.x + x_local * cos_rot - y_local * sin_rot
                y = center.y + x_local * sin_rot + y_local * cos_rot
                
                ax.plot(x, y, color='black', linewidth=0.5)

            elif e.dxftype() == 'SPLINE':
                # Basic spline support using control points
                try:
                    if hasattr(e, 'control_points'):
                        points = [(cp.x, cp.y) for cp in e.control_points]
                        if len(points) > 1:
                            x, y = zip(*points)
                            ax.plot(x, y, color='black', linewidth=0.5, linestyle='--')
                except:
                    pass  # Skip complex splines

            elif e.dxftype() == 'POINT':
                point = e.dxf.location
                ax.plot(point.x, point.y, 'o', color='black', markersize=1)

            # Add more entity types as needed
            else:
                # For unsupported entities, try to get basic geometry
                pass

        except Exception as ex:
            print(f"Error drawing {e.dxftype()}: {ex}")
            continue

def add_crop_marks(ax, xlim, ylim, mark_len=5):
    """Draw crop marks at the corners of the printable region"""
    x0, x1 = xlim
    y0, y1 = ylim
    # Bottom-left
    ax.plot([x0, x0 + mark_len], [y0, y0], color='gray', linewidth=0.5)
    ax.plot([x0, x0], [y0, y0 + mark_len], color='gray', linewidth=0.5)
    # Bottom-right
    ax.plot([x1 - mark_len, x1], [y0, y0], color='gray', linewidth=0.5)
    ax.plot([x1, x1], [y0, y0 + mark_len], color='gray', linewidth=0.5)
    # Top-left
    ax.plot([x0, x0 + mark_len], [y1, y1], color='gray', linewidth=0.5)
    ax.plot([x0, x0], [y1 - mark_len, y1], color='gray', linewidth=0.5)
    # Top-right
    ax.plot([x1 - mark_len, x1], [y1, y1], color='gray', linewidth=0.5)
    ax.plot([x1, x1], [y1 - mark_len, y1], color='gray', linewidth=0.5)

def calculate_bounding_box(msp):
    """Calculate bounding box manually for older ezdxf versions"""
    min_x = float('inf')
    min_y = float('inf')
    max_x = float('-inf')
    max_y = float('-inf')

    for entity in msp:
        try:
            if entity.dxftype() == 'LINE':
                start, end = entity.dxf.start, entity.dxf.end
                min_x = min(min_x, start.x, end.x)
                min_y = min(min_y, start.y, end.y)
                max_x = max(max_x, start.x, end.x)
                max_y = max(max_y, start.y, end.y)

            elif entity.dxftype() == 'CIRCLE':
                center, radius = entity.dxf.center, entity.dxf.radius
                min_x = min(min_x, center.x - radius)
                min_y = min(min_y, center.y - radius)
                max_x = max(max_x, center.x + radius)
                max_y = max(max_y, center.y + radius)

            elif entity.dxftype() == 'ARC':
                center, radius = entity.dxf.center, entity.dxf.radius
                # More accurate arc bounds calculation
                start_angle = math.radians(entity.dxf.start_angle)
                end_angle = math.radians(entity.dxf.end_angle)
                
                # Calculate actual arc endpoints
                start_x = center.x + radius * math.cos(start_angle)
                start_y = center.y + radius * math.sin(start_angle)
                end_x = center.x + radius * math.cos(end_angle)
                end_y = center.y + radius * math.sin(end_angle)
                
                # Start with arc endpoints
                arc_min_x = min(start_x, end_x)
                arc_max_x = max(start_x, end_x)
                arc_min_y = min(start_y, end_y)
                arc_max_y = max(start_y, end_y)
                
                # Check if arc includes extreme points (0°, 90°, 180°, 270°)
                def angle_in_arc(angle, start_deg, end_deg):
                    if start_deg <= end_deg:
                        return start_deg <= angle <= end_deg
                    else:  # Arc crosses 0°
                        return angle >= start_deg or angle <= end_deg
                
                # Check for extremes: 0° (max x), 90° (max y), 180° (min x), 270° (min y)
                if angle_in_arc(0, entity.dxf.start_angle, entity.dxf.end_angle):
                    arc_max_x = center.x + radius
                if angle_in_arc(90, entity.dxf.start_angle, entity.dxf.end_angle):
                    arc_max_y = center.y + radius
                if angle_in_arc(180, entity.dxf.start_angle, entity.dxf.end_angle):
                    arc_min_x = center.x - radius
                if angle_in_arc(270, entity.dxf.start_angle, entity.dxf.end_angle):
                    arc_min_y = center.y - radius
                
                min_x = min(min_x, arc_min_x)
                min_y = min(min_y, arc_min_y)
                max_x = max(max_x, arc_max_x)
                max_y = max(max_y, arc_max_y)

            elif entity.dxftype() == 'LWPOLYLINE':
                points = entity.get_points('xy')
                for point in points:
                    min_x = min(min_x, point[0])
                    min_y = min(min_y, point[1])
                    max_x = max(max_x, point[0])
                    max_y = max(max_y, point[1])

            elif entity.dxftype() == 'POLYLINE':
                if not entity.is_3d_polyline and not entity.is_3d_mesh:
                    points = [v.dxf.location for v in entity.vertices]
                    for point in points:
                        min_x = min(min_x, point.x)
                        min_y = min(min_y, point.y)
                        max_x = max(max_x, point.x)
                        max_y = max(max_y, point.y)

            elif entity.dxftype() == 'POINT':
                point = entity.dxf.location
                min_x = min(min_x, point.x)
                min_y = min(min_y, point.y)
                max_x = max(max_x, point.x)
                max_y = max(max_y, point.y)

            elif entity.dxftype() == 'TEXT':
                # For text, use insertion point as approximate bounds
                point = entity.dxf.insert
                min_x = min(min_x, point.x)
                min_y = min(min_y, point.y)
                max_x = max(max_x, point.x)
                max_y = max(max_y, point.y)

        except Exception as ex:
            print(f"Warning: Error calculating bounds for {entity.dxftype()}: {ex}")
            continue

    # Handle case where no entities were found
    if min_x == float('inf'):
        return 0, 0, 0, 0

    return min_x, min_y, max_x, max_y

def dxf_to_pdf_tiled(dxf_path, pdf_path, paper_size_mm=(210, 297), margin_mm=10, add_marks=True):
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()

    # Use manual bounding box calculation instead of msp.bbox()
    min_x, min_y, max_x, max_y = calculate_bounding_box(msp)
    width = max_x - min_x
    height = max_y - min_y

    # Handle case where no entities were found
    if width == 0 and height == 0:
        print("Warning: No entities found or all entities at same point")
        return

    # Auto-orient paper
    portrait = paper_size_mm[1] >= paper_size_mm[0]
    landscape_fits_better = (width > height and paper_size_mm[0] < paper_size_mm[1])
    if landscape_fits_better:
        paper_size_mm = (paper_size_mm[1], paper_size_mm[0])

    content_w = paper_size_mm[0] - 2 * margin_mm
    content_h = paper_size_mm[1] - 2 * margin_mm
    cols = math.ceil(width / content_w)
    rows = math.ceil(height / content_h)

    print(f"📐 Page size: {paper_size_mm} mm with {margin_mm} mm margin")
    print(f"🔲 Tiles: {cols} x {rows} (total: {cols * rows})")
    print(f"📏 Drawing bounds: {width:.2f} x {height:.2f}")

    with PdfPages(pdf_path) as pdf:
        for row in range(rows):
            for col in range(cols):
                x0 = min_x + col * content_w
                x1 = min(x0 + content_w, max_x)
                y0 = min_y + row * content_h
                y1 = min(y0 + content_h, max_y)

                fig = plt.figure(figsize=(paper_size_mm[0] / 25.4, paper_size_mm[1] / 25.4))
                ax = fig.add_axes([margin_mm / paper_size_mm[0],
                                   margin_mm / paper_size_mm[1],
                                   content_w / paper_size_mm[0],
                                   content_h / paper_size_mm[1]])
                ax.set_xlim(x0, x1)
                ax.set_ylim(y0, y1)
                ax.set_aspect('equal')
                ax.axis('off')

                draw_entities(msp, ax) # Pass msp to draw_entities
                if add_marks:
                    add_crop_marks(ax, (x0, x1), (y0, y1))

                pdf.savefig(fig)
                plt.close(fig)

    print(f"✅ Saved multi-page PDF with tiling to: {pdf_path}")

def parse_paper_size(size_str):
    """Parse paper size string like '210,297' or 'A4' into (width, height) in mm"""
    # Common paper sizes
    paper_sizes = {
        'A4': (210, 297),
        'A3': (297, 420),
        'A2': (420, 594),
        'A1': (594, 841),
        'A0': (841, 1189),
        'LETTER': (216, 279),
        'LEGAL': (216, 356),
        'TABLOID': (279, 432)
    }

    size_str = size_str.upper()
    if size_str in paper_sizes:
        return paper_sizes[size_str]

    # Try to parse as width,height
    try:
        parts = size_str.split(',')
        if len(parts) == 2:
            width = float(parts[0].strip())
            height = float(parts[1].strip())
            return (width, height)
    except ValueError:
        pass

    raise ValueError(f"Invalid paper size: {size_str}. Use format 'width,height' or standard size like A4, A3, etc.")

def main():
    parser = argparse.ArgumentParser(
        description='Convert DXF files to multi-page tiled PDFs for printing',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s input.dxf output.pdf
  %(prog)s drawing.dxf result.pdf --paper A3 --margin 15
  %(prog)s large_drawing.dxf tiled.pdf --paper 420,594 --margin 5

Paper sizes:
  Standard: A4, A3, A2, A1, A0, LETTER, LEGAL, TABLOID
  Custom: width,height (in mm) e.g., 210,297
        """
    )

    parser.add_argument('input_dxf',
                       help='Input DXF file path')

    parser.add_argument('output_pdf',
                       help='Output PDF file path')

    parser.add_argument('--paper', '-p',
                       default='A4',
                       help='Paper size: A4, A3, A2, A1, A0, LETTER, LEGAL, TABLOID, or width,height in mm (default: A4)')

    parser.add_argument('--margin', '-m',
                       type=float,
                       default=10.0,
                       help='Margin size in mm (default: 10)')

    parser.add_argument('--no-crop-marks',
                       action='store_true',
                       help='Disable crop marks on the output')

    args = parser.parse_args()

    try:
        paper_size = parse_paper_size(args.paper)
        add_marks = not args.no_crop_marks

        print(f"🔄 Converting: {args.input_dxf} → {args.output_pdf}")

        dxf_to_pdf_tiled(
            dxf_path=args.input_dxf,
            pdf_path=args.output_pdf,
            paper_size_mm=paper_size,
            margin_mm=args.margin,
            add_marks=add_marks
        )

    except FileNotFoundError as e:
        print(f"❌ Error: Input file not found: {args.input_dxf}")
        return 1
    except ValueError as e:
        print(f"❌ Error: {e}")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
