def calculator(db, render, **kwargs):
    end_item_id = kwargs.get("end_item", None)
    
    if not end_item_id:
        sql = """SELECT I.id, I.display_name 
                 FROM recipes R LEFT JOIN recipe_outputs RO ON R.id=RO.recipe_id 
                                LEFT JOIN item_or_machine IM ON RO.id=IM.output_id
                                LEFT JOIN items I ON I.id=IM.item_id
                                LEFT JOIN machines M on M.id=R.machine_id
                 WHERE M.name!='BuildGun'"""
        all_items = db.session.execute(sql).fetchall()
        return render("calculator_start.html", all_items=all_items)
    else:
        end_item_id = int(end_item_id)
        end_amount = int(kwargs["end_amount"])

    sql = "SELECT display_name FROM items WHERE id=:id"
    end_item = (db.session.execute(sql, {"id": end_item_id}).fetchone()[0], end_amount, end_item_id)
    
    items = {end_item_id: end_item}
    recipes = {}

    missing_id = item_loop(db, [end_item_id], recipes, kwargs)

    recipe_select = []
    if missing_id:
        sql = "SELECT display_name FROM items WHERE id=:id"
        items[missing_id] = (db.session.execute(sql, {"id": missing_id}).fetchone()[0],)
        
        sql = """SELECT R.id, R.display_name 
                 FROM recipes R LEFT JOIN recipe_outputs RO ON R.id=RO.recipe_id 
                                LEFT JOIN item_or_machine IM ON RO.id=IM.output_id
                                LEFT JOIN items I ON I.id=IM.item_id
                 WHERE I.id = :item_id"""
        query_results = db.session.execute(sql, {"item_id": missing_id}).fetchall()
        for recipe in query_results:
            recipe_select.append(recipe)

    return render("calculator.html", end_item=end_item, items=items, recipe_select=recipe_select, recipes=recipes, missing_id=missing_id)


def item_loop(db, item_ids: list, recipes: dict, kwargs: dict):
    while len(item_ids) != len(recipes):
        for item_id in item_ids:
            if item_id not in recipes:
                recipe_id = kwargs.get(f"recipe_{item_id}", None)
                if not recipe_id:
                    return item_id
                recipe_id = int(recipe_id)
                recipes[item_id] = recipe_id
                sql = """SELECT I.id
                         FROM recipes R LEFT JOIN recipe_inputs RI ON R.id=RI.recipe_id
                                        LEFT JOIN items I ON I.id=RI.item_id
                         WHERE R.id=:recipe_id"""
                ids_to_add = db.session.execute(sql, {"recipe_id": recipe_id}).fetchall()
                for add_id in ids_to_add:
                    item_ids.append(add_id[0])