from flask import Flask
from flask import jsonify
from flask.templating import render_template
import fdb

database = {"host": "127.0.0.1", "database": "waitress",
            "user": "SYSDBA", "password": "masterkey"}
app = Flask(__name__)


def con_to_firebird(query, *args):
    con = fdb.connect(**database)
    cur = con.cursor()
    try:
        cur.execute(query, *args)
    except fdb.Error as e:
        print(e)
    else:
        for line in cur.fetchall():
            yield line
    finally:
        con.close()


@app.route('/')
def table():
    query = """
    select
    smetka.id,
    smetka.name,
    users.name_cyr,
    sum(smetka_el.suma),
    max(opr.date_time)
    from smetka_el
    inner join opr on opr.id = smetka_el.opr_id
    inner join smetka on smetka.id = opr.smetka_id
    inner join users on users.id = smetka.otc_user_id
    where smetka.close_opr_id is null
    group by 1, 2, 3
    order by 4 desc
    """
    fdb_data = con_to_firebird(query)
    return render_template('index.html', data=fdb_data)


@app.route('/info/<int:id>/', methods=['GET'])
def detail_table(id):
    result = []
    query_details = """
    select
    kits.name_cyr,
    cast(smetka_el.kol as int),
    smetka_el.cena,
    cast(coalesce(smetka_el.procent, 0) as int),
    smetka_el.suma
    from smetka_el
    inner join opr on opr.id = smetka_el.opr_id
    inner join kits on kits.id = smetka_el.kit_id
    where opr.smetka_id = {id}
    """.format(id=id)
    fdb_data = con_to_firebird(query_details)
    for line in fdb_data:
        result.append(line)
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
