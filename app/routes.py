from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user
)
from sqlalchemy import text
from werkzeug.security import (
    check_password_hash,
    generate_password_hash
)
from app import db
from app.models import User, Asset, Incident, IncidentHistory, IncidentComment


main = Blueprint("main", __name__)
def generate_incident_number():
    last_incident = Incident.query.order_by(
        Incident.id.desc()
    ).first()

    if last_incident:
        next_id = last_incident.id + 1
    else:
        next_id = 1

    return f"INC-{next_id:05d}"


@main.route("/")
def index():
    return render_template("index.html")


@main.route("/db-test")
def db_test():
    try:
        result = db.session.execute(text("SELECT 1")).scalar()

        if result == 1:
            return "Database connection successful!"

        return "Database connection failed.", 500

    except Exception as e:
        return f"Database connection failed: {e}", 500


@main.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)

            return redirect(url_for("main.dashboard"))

        return render_template(
            "login.html",
            error="Invalid email or password."
        )

    return render_template("login.html")


@main.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.login"))


@main.route("/dashboard")
@login_required
def dashboard():

    if current_user.role == "ADMIN":

        total_users = User.query.count()
        total_assets = Asset.query.count()
        total_incidents = Incident.query.count()

        open_incidents = Incident.query.filter_by(
            status="OPEN"
        ).count()

        assigned_incidents = Incident.query.filter_by(
            status="ASSIGNED"
        ).count()

        in_progress_incidents = Incident.query.filter_by(
            status="IN_PROGRESS"
        ).count()

        resolved_incidents = Incident.query.filter_by(
            status="RESOLVED"
        ).count()
        closed_incidents = Incident.query.filter_by(
    status="CLOSED"
).count()

        return render_template(
            "dashboard.html",
            total_users=total_users,
            total_assets=total_assets,
            total_incidents=total_incidents,
            open_incidents=open_incidents,
            assigned_incidents=assigned_incidents,
            in_progress_incidents=in_progress_incidents,
            resolved_incidents=resolved_incidents,
            closed_incidents=closed_incidents
        )

    elif current_user.role == "TECHNICIAN":

        assigned_incidents = Incident.query.filter_by(
            assigned_to=current_user.id
        ).count()

        open_incidents = Incident.query.filter_by(
            assigned_to=current_user.id,
            status="ASSIGNED"
        ).count()

        in_progress_incidents = Incident.query.filter_by(
            assigned_to=current_user.id,
            status="IN_PROGRESS"
        ).count()

        resolved_incidents = Incident.query.filter_by(
            assigned_to=current_user.id,
            status="RESOLVED"
        ).count()
        closed_incidents = Incident.query.filter_by(
    assigned_to=current_user.id,
    status="CLOSED"
).count()

        return render_template(
            "dashboard.html",
            assigned_incidents=assigned_incidents,
            open_incidents=open_incidents,
            in_progress_incidents=in_progress_incidents,
            resolved_incidents=resolved_incidents,
            closed_incidents=closed_incidents
        )

    else:

        my_assets = Asset.query.filter_by(
            assigned_to=current_user.id
        ).count()

        my_incidents = Incident.query.filter_by(
            reported_by=current_user.id
        ).count()

        open_incidents = Incident.query.filter_by(
            reported_by=current_user.id,
            status="OPEN"
        ).count()

        resolved_incidents = Incident.query.filter_by(
            reported_by=current_user.id,
            status="RESOLVED"
        ).count()
        closed_incidents = Incident.query.filter_by(
    reported_by=current_user.id,
    status="CLOSED"
).count()

        return render_template(
            "dashboard.html",
            my_assets=my_assets,
            my_incidents=my_incidents,
            open_incidents=open_incidents,
            resolved_incidents=resolved_incidents,
            closed_incidents=closed_incidents
        )
@main.route("/analytics")
@login_required
def analytics():

    if current_user.role != "ADMIN":
        return "Access denied.", 403

    # Incident counts by status
    open_count = Incident.query.filter_by(
        status="OPEN"
    ).count()

    assigned_count = Incident.query.filter_by(
        status="ASSIGNED"
    ).count()

    in_progress_count = Incident.query.filter_by(
        status="IN_PROGRESS"
    ).count()

    resolved_count = Incident.query.filter_by(
        status="RESOLVED"
    ).count()

    closed_count = Incident.query.filter_by(
        status="CLOSED"
    ).count()

    # Incident counts by priority
    critical_count = Incident.query.filter_by(
        priority="CRITICAL"
    ).count()

    high_count = Incident.query.filter_by(
        priority="HIGH"
    ).count()

    medium_count = Incident.query.filter_by(
        priority="MEDIUM"
    ).count()

    low_count = Incident.query.filter_by(
        priority="LOW"
    ).count()

    # Technician workload
    technicians = User.query.filter_by(
        role="TECHNICIAN"
    ).order_by(
        User.name
    ).all()

    technician_stats = []

    for technician in technicians:

        assigned = Incident.query.filter_by(
            assigned_to=technician.id
        ).count()

        active = Incident.query.filter(
            Incident.assigned_to == technician.id,
            Incident.status.in_([
                "ASSIGNED",
                "IN_PROGRESS"
            ])
        ).count()

        resolved = Incident.query.filter_by(
            assigned_to=technician.id,
            status="RESOLVED"
        ).count()

        closed = Incident.query.filter_by(
            assigned_to=technician.id,
            status="CLOSED"
        ).count()

        technician_stats.append({
            "name": technician.name,
            "assigned": assigned,
            "active": active,
            "resolved": resolved,
            "closed": closed
        })

    # Recent incidents
    recent_incidents = Incident.query.order_by(
        Incident.created_at.desc()
    ).limit(10).all()

    return render_template(
        "analytics.html",
        open_count=open_count,
        assigned_count=assigned_count,
        in_progress_count=in_progress_count,
        resolved_count=resolved_count,
        closed_count=closed_count,
        critical_count=critical_count,
        high_count=high_count,
        medium_count=medium_count,
        low_count=low_count,
        technician_stats=technician_stats,
        recent_incidents=recent_incidents
    )
@main.route("/users")
@login_required
def users():

    if current_user.role != "ADMIN":
        return "Access denied.", 403

    users = User.query.order_by(User.id).all()

    return render_template(
        "users.html",
        users=users
    )
@main.route("/users/add", methods=["GET", "POST"])
@login_required
def add_user():

    if current_user.role != "ADMIN":
        return "Access denied.", 403

    if request.method == "POST":

        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("role")

        # Check whether email already exists
        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            return render_template(
                "add_user.html",
                error="A user with this email already exists."
            )

        # Create user with hashed password
        new_user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            role=role
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("main.users"))

    return render_template("add_user.html")

@main.route("/assets")
@login_required
def assets():

    if current_user.role != "ADMIN":
        return "Access denied.", 403

    assets = Asset.query.order_by(Asset.id).all()

    users = User.query.all()

    users_by_id = {
        user.id: user
        for user in users
    }

    return render_template(
        "assets.html",
        assets=assets,
        users_by_id=users_by_id
    )
@main.route("/assets/add", methods=["GET", "POST"])
@login_required
def add_asset():

    if current_user.role != "ADMIN":
        return "Access denied.", 403

    employees = User.query.filter_by(role="EMPLOYEE").order_by(User.name).all()

    if request.method == "POST":

        asset_tag = request.form.get("asset_tag")
        name = request.form.get("name")
        asset_type = request.form.get("asset_type")
        serial_number = request.form.get("serial_number")
        department = request.form.get("department")
        location = request.form.get("location")
        status = request.form.get("status")
        purchase_date = request.form.get("purchase_date")
        warranty_expiry = request.form.get("warranty_expiry")
        assigned_to = request.form.get("assigned_to")

        # Check asset tag
        existing_asset = Asset.query.filter_by(
            asset_tag=asset_tag
        ).first()

        if existing_asset:
            return render_template(
                "add_asset.html",
                error="An asset with this asset tag already exists.",
                employees=employees
            )

        # Check serial number
        if serial_number:

            existing_serial = Asset.query.filter_by(
                serial_number=serial_number
            ).first()

            if existing_serial:
                return render_template(
                    "add_asset.html",
                    error="An asset with this serial number already exists.",
                    employees=employees
                )

        # Validate employee
        assigned_user_id = None

        if assigned_to:
            assigned_user = User.query.filter_by(
                id=int(assigned_to),
                role="EMPLOYEE"
            ).first()

            if not assigned_user:
                return render_template(
                    "add_asset.html",
                    error="Invalid employee selected.",
                    employees=employees
                )

            assigned_user_id = assigned_user.id

        new_asset = Asset(
            asset_tag=asset_tag,
            name=name,
            asset_type=asset_type,
            serial_number=serial_number or None,
            department=department or None,
            location=location or None,
            assigned_to=assigned_user_id,
            status=status,
            purchase_date=purchase_date or None,
            warranty_expiry=warranty_expiry or None
        )

        db.session.add(new_asset)
        db.session.commit()

        return redirect(url_for("main.assets"))

    return render_template(
        "add_asset.html",
        employees=employees
    )
@main.route("/my-assets")
@login_required
def my_assets():
    if current_user.role != "EMPLOYEE":
        return "Access denied.", 403

    assets = Asset.query.filter_by(
        assigned_to=current_user.id
    ).all()

    return render_template(
        "my_assets.html",
        assets=assets
    )
@main.route("/my-incidents")
@login_required
def my_incidents():

    if current_user.role != "EMPLOYEE":
        return "Access denied.", 403

    incidents = Incident.query.filter_by(
        reported_by=current_user.id
    ).order_by(
        Incident.created_at.desc()
    ).all()

    return render_template(
        "my_incidents.html",
        incidents=incidents
    )
@main.route("/incidents/report", methods=["GET", "POST"])
@login_required
def report_incident():

    if current_user.role != "EMPLOYEE":
        return "Access denied.", 403

    # Get assets assigned to the logged-in employee
    assets = Asset.query.filter_by(
        assigned_to=current_user.id
    ).order_by(
        Asset.name
    ).all()

    if request.method == "POST":

        asset_id = request.form.get("asset_id")
        title = request.form.get("title")
        description = request.form.get("description")
        priority = request.form.get("priority")

        # Verify that the selected asset belongs to this employee
        asset = Asset.query.filter_by(
            id=asset_id,
            assigned_to=current_user.id
        ).first()

        if not asset:
            return render_template(
                "report_incident.html",
                assets=assets,
                error="Invalid asset selected."
            )

        incident = Incident(
            incident_number=generate_incident_number(),
            title=title,
            description=description,
            asset_id=asset.id,
            reported_by=current_user.id,
            priority=priority,
            status="OPEN"
        )

        db.session.add(incident)
        db.session.commit()

        return redirect(
            url_for("main.my_incidents")
        )

    return render_template(
        "report_incident.html",
        assets=assets
    )
@main.route("/incidents")
@login_required
def incidents():

    if current_user.role != "ADMIN":
        return "Access denied.", 403

    incidents = Incident.query.order_by(
        Incident.created_at.desc()
    ).all()

    technicians = User.query.filter_by(
        role="TECHNICIAN"
    ).order_by(
        User.name
    ).all()

    return render_template(
        "incidents.html",
        incidents=incidents,
        technicians=technicians
    )
@main.route(
    "/incidents/<int:incident_id>/close",
    methods=["POST"]
)
@login_required
def close_incident(incident_id):

    if current_user.role != "ADMIN":
        return "Access denied.", 403

    incident = Incident.query.get_or_404(incident_id)

    if incident.status != "RESOLVED":
        return "Only resolved incidents can be closed.", 400

    old_status = incident.status

    incident.status = "CLOSED"

    history = IncidentHistory(
        incident_id=incident.id,
        changed_by=current_user.id,
        old_status=old_status,
        new_status="CLOSED",
        comment="Incident closed by administrator."
    )

    db.session.add(history)
    db.session.commit()

    return redirect(
        url_for(
            "main.incident_details",
            incident_id=incident.id
        )
    )


@main.route("/incidents/<int:incident_id>")
@login_required
def incident_details(incident_id):

    if current_user.role != "ADMIN":
        return "Access denied.", 403

    incident = Incident.query.get_or_404(incident_id)

    technicians = User.query.filter_by(
        role="TECHNICIAN"
    ).order_by(
        User.name
    ).all()

    return render_template(
        "incident_details.html",
        incident=incident,
        technicians=technicians
    )


@main.route(
    "/incidents/<int:incident_id>/assign",
    methods=["POST"]
)
@login_required
def assign_incident(incident_id):

    if current_user.role != "ADMIN":
        return "Access denied.", 403

    incident = Incident.query.get_or_404(incident_id)

    technician_id = request.form.get("technician_id")

    technician = User.query.filter_by(
        id=technician_id,
        role="TECHNICIAN"
    ).first()

    if not technician:
        return "Invalid technician selected.", 400

    old_status = incident.status

    incident.assigned_to = technician.id

    if incident.status == "OPEN":
        incident.status = "ASSIGNED"

    history = IncidentHistory(
        incident_id=incident.id,
        changed_by=current_user.id,
        old_status=old_status,
        new_status=incident.status,
        comment=f"Incident assigned to {technician.name}"
    )

    db.session.add(history)
    db.session.commit()

    return redirect(
        url_for(
            "main.incident_details",
            incident_id=incident.id
        )
    )
@main.route("/technician/incidents")
@login_required
def technician_incidents():

    if current_user.role != "TECHNICIAN":
        return "Access denied.", 403

    incidents = Incident.query.filter_by(
        assigned_to=current_user.id
    ).order_by(
        Incident.created_at.desc()
    ).all()

    return render_template(
        "technician_incidents.html",
        incidents=incidents
    )
@main.route("/technician/incidents/<int:incident_id>")
@login_required
def technician_incident_details(incident_id):

    if current_user.role != "TECHNICIAN":
        return "Access denied.", 403

    incident = Incident.query.get_or_404(incident_id)

    if incident.assigned_to != current_user.id:
        return "You are not assigned to this incident.", 403

    return render_template(
        "technician_incident_details.html",
        incident=incident
    )


@main.route(
    "/technician/incidents/<int:incident_id>/update",
    methods=["POST"]
)
@login_required
def update_incident_status(incident_id):

    if current_user.role != "TECHNICIAN":
        return "Access denied.", 403

    incident = Incident.query.get_or_404(incident_id)

    if incident.assigned_to != current_user.id:
        return "You are not assigned to this incident.", 403

    new_status = request.form.get("status")
    resolution = request.form.get("resolution")

    allowed_statuses = [
        "IN_PROGRESS",
        "RESOLVED"
    ]

    if new_status not in allowed_statuses:
        return "Invalid status.", 400

    old_status = incident.status

    incident.status = new_status

    if resolution:
        incident.resolution = resolution

    if new_status == "RESOLVED":
        from datetime import datetime
        incident.resolved_at = datetime.utcnow()

    history = IncidentHistory(
        incident_id=incident.id,
        changed_by=current_user.id,
        old_status=old_status,
        new_status=new_status,
        comment=resolution or "Status updated"
    )

    db.session.add(history)
    db.session.commit()

    return redirect(
        url_for(
            "main.technician_incident_details",
            incident_id=incident.id
        )
    )
@main.route(
    "/technician/incidents/<int:incident_id>/comment",
    methods=["POST"]
)
@login_required
def add_incident_comment(incident_id):

    if current_user.role != "TECHNICIAN":
        return "Access denied.", 403

    incident = Incident.query.get_or_404(incident_id)

    if incident.assigned_to != current_user.id:
        return "You are not assigned to this incident.", 403

    comment_text = request.form.get("comment", "").strip()

    if not comment_text:
        return "Comment cannot be empty.", 400

    comment = IncidentComment(
        incident_id=incident.id,
        user_id=current_user.id,
        comment=comment_text
    )

    db.session.add(comment)
    db.session.commit()

    return redirect(
        url_for(
            "main.technician_incident_details",
            incident_id=incident.id
        )
    )


@main.route(
    "/incidents/<int:incident_id>/comment",
    methods=["POST"]
)
@login_required
def admin_add_incident_comment(incident_id):

    if current_user.role != "ADMIN":
        return "Access denied.", 403

    incident = Incident.query.get_or_404(incident_id)

    comment_text = request.form.get("comment", "").strip()

    if not comment_text:
        return "Comment cannot be empty.", 400

    comment = IncidentComment(
        incident_id=incident.id,
        user_id=current_user.id,
        comment=comment_text
    )

    db.session.add(comment)
    db.session.commit()

    return redirect(
        url_for(
            "main.incident_details",
            incident_id=incident.id
        )
    )