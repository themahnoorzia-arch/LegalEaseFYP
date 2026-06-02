from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from db.db import get_pg_connection
import psycopg2.extras

registrar_bp = Blueprint('registrar', __name__)


@registrar_bp.route('/merge-cases', methods=['POST'])
@login_required
def merge_cases():
    if current_user.role != 'CourtRegistrar':
        return jsonify({'error': 'Forbidden'}), 403

    data = request.get_json() or {}
    keep_id = data.get('keep_id')
    discard_id = data.get('discard_id')

    try:
        keep_id = int(keep_id)
        discard_id = int(discard_id)
    except (TypeError, ValueError):
        return jsonify({
            'error': 'keep_id and discard_id must be integers'
        }), 400

    conn = None
    try:
        conn = get_pg_connection()
        cur = conn.cursor()
        cur.execute('SELECT merge_cases(%s, %s)', (keep_id, discard_id))
        conn.commit()
        return jsonify({'message': 'Cases merged successfully'}), 200

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'error': str(e)}), 500

    finally:
        if conn:
            conn.close()


@registrar_bp.route('/join-requests', methods=['GET'])
@login_required
def list_join_requests():
    if current_user.role != 'CourtRegistrar':
        return jsonify({'error': 'Forbidden'}), 403

    conn = None
    try:
        conn = get_pg_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # check if caselawyeraccess has a status column
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='caselawyeraccess' AND column_name='status'")
        has_status = cur.fetchone() is not None

        if not has_status:
            # No status column — nothing to list as pending
            return jsonify([]), 200

        cur.execute(
            """
            SELECT
                cla.caseid,
                c.title AS case_name,
                c.casenumber,
                cla.lawyerid,
                COALESCE(u.firstname || ' ' || u.lastname, l.name) AS lawyer_name,
                cla.side
            FROM caselawyeraccess cla
            JOIN cases c ON cla.caseid = c.caseid
            LEFT JOIN lawyer l ON cla.lawyerid = l.lawyerid
            LEFT JOIN users u ON l.userid = u.userid
            WHERE cla.status = 'pending'
            ORDER BY cla.caseid
            """
        )

        rows = cur.fetchall()
        # convert RealDictRows to plain dicts
        results = [dict(r) for r in rows]
        return jsonify(results), 200

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'error': str(e)}), 500

    finally:
        if conn:
            conn.close()


@registrar_bp.route('/join-requests/<int:lawyerid>/<int:caseid>/approve', methods=['POST'])
@login_required
def approve_join_request(lawyerid, caseid):
    if current_user.role != 'CourtRegistrar':
        return jsonify({'error': 'Forbidden'}), 403

    conn = None
    try:
        conn = get_pg_connection()
        cur = conn.cursor()

        # check for status column
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='caselawyeraccess' AND column_name='status'")
        has_status = cur.fetchone() is not None

        if has_status:
            cur.execute("UPDATE caselawyeraccess SET status = 'approved' WHERE lawyerid = %s AND caseid = %s", (lawyerid, caseid))
            if cur.rowcount == 0:
                conn.rollback()
                return jsonify({'error': 'Join request not found'}), 404
        else:
            # No status column — just confirm the row exists
            cur.execute("SELECT 1 FROM caselawyeraccess WHERE lawyerid = %s AND caseid = %s", (lawyerid, caseid))
            if not cur.fetchone():
                return jsonify({'error': 'Join request not found'}), 404

        conn.commit()
        return jsonify({'message': 'Join request approved'}), 200

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'error': str(e)}), 500

    finally:
        if conn:
            conn.close()


@registrar_bp.route('/join-requests/<int:lawyerid>/<int:caseid>/reject', methods=['POST'])
@login_required
def reject_join_request(lawyerid, caseid):
    if current_user.role != 'CourtRegistrar':
        return jsonify({'error': 'Forbidden'}), 403

    conn = None
    try:
        conn = get_pg_connection()
        cur = conn.cursor()

        # Delete the request row if present
        cur.execute("DELETE FROM caselawyeraccess WHERE lawyerid = %s AND caseid = %s", (lawyerid, caseid))
        if cur.rowcount == 0:
            conn.rollback()
            return jsonify({'error': 'Join request not found'}), 404

        conn.commit()
        return jsonify({'message': 'Join request rejected'}), 200

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'error': str(e)}), 500

    finally:
        if conn:
            conn.close()
