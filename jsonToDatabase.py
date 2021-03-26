"""
This file is for creating a database from Docs.json in the Satisfactory game folder.
Docs.json is not included in GitHub, because it is not owned by me.
"""

from json import load
from sqlalchemy import create_engine, text
from sqlalchemy_utils import database_exists, drop_database, create_database
from os.path import isfile
from os import getenv

from dotenv import load_dotenv
load_dotenv()


def itemSifter(items_string: str):
    items = []

    quotes = 0
    start = 0
    end = 0
    amount = 0
    now_amount = False
    for i in range(len(items_string)):
        if items_string[i] == ".":
            start = i+1

        elif items_string[i] == '"':
            quotes += 1
            if quotes == 2:
                quotes = 0
                end = i
                name = items_string[start:end-2]
                if name.startswith("Desc_"):
                    name = name[5:]
                elif name.startswith("BP_"):
                    name = name[3:]
                now_amount = True

        elif now_amount:
            if items_string[i] == "=":
                start = i+1
            elif items_string[i] == ")":
                end = i
                now_amount = False
                amount = int(items_string[start:end])
                items.append((name, amount))

    return items


def jsonConverter():
    print("Started reading Docs file...")
    with open("Docs.json", encoding="utf-16") as file:
        data = load(file)
    
    items = []
    machines = []
    recipes = []

    for item in data:
        native_class = item["NativeClass"]
        if native_class in ("Class'/Script/FactoryGame.FGItemDescriptor'", "Class'/Script/FactoryGame.FGResourceDescriptor'", "Class'/Script/FactoryGame.FGEquipmentDescriptor'", "Class'/Script/FactoryGame.FGConsumableDescriptor'", "Class'/Script/FactoryGame.FGItemDescriptorBiomass'"):
            items_list = item["Classes"]

            stack_sizes = {"SS_HUGE": 500, "SS_BIG": 200, "SS_MEDIUM": 100, "SS_SMALL": 50, "SS_ONE": 1, "SS_FLUID": 0}

            for item in items_list:
                name = item["ClassName"][:-2]
                if name.startswith("Desc_"):
                    name = name[5:]
                elif name.startswith("BP_"):
                    name = name[3:]
                display_name = item["mDisplayName"]
                description = " ".join(item["mDescription"].split())
                stack_size = stack_sizes[item["mStackSize"]]
                sink_points = int(item["mResourceSinkPoints"])
                items.append((name, display_name, description, stack_size, sink_points))

        elif native_class == "Class'/Script/FactoryGame.FGRecipe'":
            recipes_list = item["Classes"]

            for item in recipes_list:
                name = item["ClassName"][7:-2]
                display_name = item["mDisplayName"]
                time = int(float(item["mManufactoringDuration"]))
                ingredients = itemSifter(item["mIngredients"])
                products = itemSifter(item["mProduct"])
                producers_string = item["mProducedIn"]
                producers = []
                start = 0
                end = 0
                for i in range(len(producers_string)):
                    if producers_string[i] == ".":
                        start = i+1
                    elif producers_string[i] in ",)":
                        end = i
                        producer = producers_string[start:end]
                        if producer.endswith("_C"):
                            producer = producer[:-2]
                        if producer.startswith("Build_"):
                            producer = producer[6:]
                        elif producer.startswith("BP_"):
                            producer = producer[3:]
                        elif producer.startswith("FG"):
                            producer = producer[2:]
                        producers.append(producer)

                recipes.append((name, display_name, time, ingredients, products, producers))

        elif native_class in ("Class'/Script/FactoryGame.FGBuildableManufacturer'", "Class'/Script/FactoryGame.FGBuildableResourceExtractor'", "Class'/Script/FactoryGame.FGBuildableWaterPump'"):
            machines_list = item["Classes"]

            for item in machines_list:
                name = item["ClassName"][6:-2]
                display_name = item["mDisplayName"]
                description = " ".join(item["mDescription"].split())
                machines.append((name, display_name, description))

    print("File reading done!")
    return items, recipes, machines


def createDatabase():
    print("Started creating database...")
    
    database_url = getenv("DATABASE_URL")

    if database_exists(database_url):
        print("Dropping old database...")
        drop_database(database_url)

    create_database(database_url)
    print("Database created!")

    db = create_engine(database_url)

    print("Started creating tables from schema...")
    in_progress = ""
    with open("schema.sql") as file:
        for line in file:
            in_progress += " ".join(line.split())
            if in_progress.endswith(";"):
                command = in_progress
                in_progress = ""
                db.execute(command)

    print("Tables created!")
    return db


def insertToDatabase():
    if not isfile("Docs.json"):
        print("Docs file required from Satisfactory, located in:")
        print("/(satisfactory-game-folder)/CommunityResources/Docs")
        return

    try:
        items, recipes, machines = jsonConverter()
    except:
        print("Could not read Docs file, make sure it is the correct one from:")
        print("/(satisfactory-game-folder)/CommunityResources/Docs")
        return

    db = createDatabase()

    print("Started database insert...")
    names = []
    machines_names = ["BuildGun"]

    sql = text("INSERT INTO items (name, display_name, description, stack_size, sink_points) VALUES (:name, :display_name, :description, :stack_size, :sink_points)")
    for item in items:
        names.append(item[0])
        db.execute(sql, {"name": item[0], "display_name": item[1], "description": item[2], "stack_size": item[3], "sink_points": item[4]})
    
    print("Items inserted!")

    sql = text("INSERT INTO machines (name, display_name, description) VALUES (:name, :display_name, :description)")
    db.execute(sql, {"name": "BuildGun", "display_name": "Build Gun", "description": "Build Gun"})
    for machine in machines:
        names.append(machine[0])
        machines_names.append(machine[0])
        db.execute(sql, {"name": machine[0], "display_name": machine[1], "description": machine[2]})
    
    print("Machines inserted!")

    sql = text("INSERT INTO recipes (name, display_name, time, machine_id) VALUES (:name, :display_name, :time, :machine_id) RETURNING id")
    sql_input = text("INSERT INTO recipe_inputs (recipe_id, item_id, amount) VALUES (:recipe_id, :item_id, :amount)")
    sql_output = text("INSERT INTO recipe_outputs (recipe_id, output_id, amount, is_machine) VALUES (:recipe_id, :output_id, :amount, :is_machine)")
    sql_output_item = text("INSERT INTO item_or_machine (item_id) VALUES (:item_id) RETURNING id")
    sql_output_machine = text("INSERT INTO item_or_machine (machine_id) VALUES (:machine_id) RETURNING id")
    for recipe in recipes:
        inputs = recipe[3]
        outputs = recipe[4]
        producers = recipe[5]
        
        if [i for i in inputs if i[0] in names] and [i for i in outputs if i[0] in names] and [i for i in producers if i in machines_names]:
            producer = [i for i in producers if i not in ("WorkBenchComponent", "WorkshopComponent", "BuildableAutomatedWorkBench")][0]
            machine_id = db.execute(text("SELECT id FROM machines WHERE name = :name"), {"name": producer}).fetchone()[0]
            recipe_id = db.execute(sql, {"name": recipe[0], "display_name": recipe[1], "time": recipe[2], "machine_id": machine_id}).fetchone()[0]
            
            for item in inputs:
                item_id = db.execute(text("SELECT id FROM items WHERE name = :name"), {"name": item[0]}).fetchone()[0]
                db.execute(sql_input, {"recipe_id": recipe_id, "item_id": item_id, "amount": item[1]})
            
            for item in outputs:
                if item[0] in machines_names:
                    machine_id = db.execute(text("SELECT id FROM machines WHERE name = :name"), {"name": item[0]}).fetchone()[0]
                    output_id = db.execute(sql_output_machine, {"machine_id": machine_id}).fetchone()[0]
                    is_machine = True
                else:
                    item_id = db.execute(text("SELECT id FROM items WHERE name = :name"), {"name": item[0]}).fetchone()[0]
                    output_id = db.execute(sql_output_item, {"item_id": item_id}).fetchone()[0]
                    is_machine = False

                db.execute(sql_output, {"recipe_id": recipe_id, "output_id": output_id, "amount": item[1], "is_machine": is_machine})

    print("Recipes inserted!")

    print("Database complete!")


if __name__ == "__main__":
    insertToDatabase()