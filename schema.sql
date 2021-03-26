CREATE TABLE "items" (
  "id" serial PRIMARY KEY,
  "name" text,
  "display_name" text,
  "description" text,
  "stack_size" int,
  "sink_points" int
);

CREATE TABLE "recipes" (
  "id" serial PRIMARY KEY,
  "name" text,
  "display_name" text,
  "time" int,
  "machine_id" int
);

CREATE TABLE "recipe_inputs" (
  "id" serial PRIMARY KEY,
  "recipe_id" int,
  "item_id" int,
  "amount" int
);

CREATE TABLE "recipe_outputs" (
  "id" serial PRIMARY KEY,
  "recipe_id" int,
  "output_id" int,
  "amount" int,
  "is_machine" boolean
);

CREATE TABLE "item_or_machine" (
  "id" serial PRIMARY KEY,
  "item_id" int,
  "machine_id" int
);

CREATE TABLE "machines" (
  "id" serial PRIMARY KEY,
  "name" text,
  "display_name" text,
  "description" text
);

ALTER TABLE "recipe_inputs" ADD FOREIGN KEY ("item_id") REFERENCES "items" ("id");

ALTER TABLE "recipe_inputs" ADD FOREIGN KEY ("recipe_id") REFERENCES "recipes" ("id");

ALTER TABLE "recipe_outputs" ADD FOREIGN KEY ("output_id") REFERENCES "item_or_machine" ("id");

ALTER TABLE "item_or_machine" ADD FOREIGN KEY ("item_id") REFERENCES "items" ("id");

ALTER TABLE "item_or_machine" ADD FOREIGN KEY ("machine_id") REFERENCES "machines" ("id");

ALTER TABLE "recipe_outputs" ADD FOREIGN KEY ("recipe_id") REFERENCES "recipes" ("id");

ALTER TABLE "recipes" ADD FOREIGN KEY ("machine_id") REFERENCES "machines" ("id");
