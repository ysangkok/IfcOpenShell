import os
import bpy
import json
import time
import pystache
import webbrowser
import ifcopenshell.api
import ifcopenshell.util.date
from datetime import datetime
from dateutil import parser
from blenderbim.bim.ifc import IfcStore
from bpy_extras.io_utils import ImportHelper
from ifcopenshell.api.sequence.data import Data


class AddWorkPlan(bpy.types.Operator):
    bl_idname = "bim.add_work_plan"
    bl_label = "Add Work Plan"

    def execute(self, context):
        ifcopenshell.api.run("sequence.add_work_plan", IfcStore.get_file())
        Data.load(IfcStore.get_file())
        return {"FINISHED"}


class EditWorkPlan(bpy.types.Operator):
    bl_idname = "bim.edit_work_plan"
    bl_label = "Edit Work Plan"

    def execute(self, context):
        props = context.scene.BIMWorkPlanProperties
        attributes = {}
        for attribute in props.work_plan_attributes:
            if attribute.is_null:
                attributes[attribute.name] = None
            else:
                if attribute.data_type == "string":
                    attributes[attribute.name] = attribute.string_value
                elif attribute.data_type == "enum":
                    attributes[attribute.name] = attribute.enum_value
        self.file = IfcStore.get_file()
        ifcopenshell.api.run(
            "sequence.edit_work_plan",
            self.file,
            **{"work_plan": self.file.by_id(props.active_work_plan_id), "attributes": attributes},
        )
        Data.load(IfcStore.get_file())
        bpy.ops.bim.disable_editing_work_plan()
        return {"FINISHED"}


class RemoveWorkPlan(bpy.types.Operator):
    bl_idname = "bim.remove_work_plan"
    bl_label = "Remove Work Plan"
    work_plan: bpy.props.IntProperty()

    def execute(self, context):
        self.file = IfcStore.get_file()
        ifcopenshell.api.run("sequence.remove_work_plan", self.file, **{"work_plan": self.file.by_id(self.work_plan)})
        Data.load(IfcStore.get_file())
        return {"FINISHED"}


class EnableEditingWorkPlan(bpy.types.Operator):
    bl_idname = "bim.enable_editing_work_plan"
    bl_label = "Enable Editing Work Plan"
    work_plan: bpy.props.IntProperty()

    def execute(self, context):
        props = context.scene.BIMWorkPlanProperties
        while len(props.work_plan_attributes) > 0:
            props.work_plan_attributes.remove(0)

        data = Data.work_plans[self.work_plan]

        for attribute in IfcStore.get_schema().declaration_by_name("IfcWorkPlan").all_attributes():
            data_type = ifcopenshell.util.attribute.get_primitive_type(attribute)
            if data_type == "entity":
                continue
            new = props.work_plan_attributes.add()
            new.name = attribute.name()
            new.is_null = data[attribute.name()] is None
            new.is_optional = attribute.optional()
            new.data_type = data_type
            if attribute.name() in ["CreationDate", "StartTime", "FinishTime"]:
                new.string_value = "" if new.is_null else data[attribute.name()].isoformat()
            elif data_type == "string":
                new.string_value = "" if new.is_null else data[attribute.name()]
            elif data_type == "enum":
                new.enum_items = json.dumps(ifcopenshell.util.attribute.get_enum_items(attribute))
                if data[attribute.name()]:
                    new.enum_value = data[attribute.name()]
        props.active_work_plan_id = self.work_plan
        props.editing_type = "ATTRIBUTES"
        return {"FINISHED"}


class DisableEditingWorkPlan(bpy.types.Operator):
    bl_idname = "bim.disable_editing_work_plan"
    bl_label = "Disable Editing Work Plan"

    def execute(self, context):
        context.scene.BIMWorkPlanProperties.active_work_plan_id = 0
        return {"FINISHED"}


class EnableEditingWorkPlanSchedules(bpy.types.Operator):
    bl_idname = "bim.enable_editing_work_plan_schedules"
    bl_label = "Enable Editing Work Plan Schedules"
    work_plan: bpy.props.IntProperty()

    def execute(self, context):
        props = context.scene.BIMWorkPlanProperties
        props.active_work_plan_id = self.work_plan
        props.editing_type = "SCHEDULES"
        return {"FINISHED"}


class AssignWorkSchedule(bpy.types.Operator):
    bl_idname = "bim.assign_work_schedule"
    bl_label = "Assign Work Schedule"
    work_plan: bpy.props.IntProperty()
    work_schedule: bpy.props.IntProperty()

    def execute(self, context):
        self.file = IfcStore.get_file()
        ifcopenshell.api.run(
            "aggregate.assign_object",
            self.file,
            **{
                "relating_object": self.file.by_id(self.work_plan),
                "product": self.file.by_id(self.work_schedule),
            },
        )
        Data.load(IfcStore.get_file())
        return {"FINISHED"}


class UnassignWorkSchedule(bpy.types.Operator):
    bl_idname = "bim.unassign_work_schedule"
    bl_label = "Unassign Work Schedule"
    work_plan: bpy.props.IntProperty()
    work_schedule: bpy.props.IntProperty()

    def execute(self, context):
        self.file = IfcStore.get_file()
        ifcopenshell.api.run(
            "aggregate.unassign_object",
            self.file,
            **{
                "relating_object": self.file.by_id(self.work_plan),
                "product": self.file.by_id(self.work_schedule),
            },
        )
        Data.load(IfcStore.get_file())
        return {"FINISHED"}


class AddWorkSchedule(bpy.types.Operator):
    bl_idname = "bim.add_work_schedule"
    bl_label = "Add Work Schedule"

    def execute(self, context):
        ifcopenshell.api.run("sequence.add_work_schedule", IfcStore.get_file())
        Data.load(IfcStore.get_file())
        return {"FINISHED"}


class EditWorkSchedule(bpy.types.Operator):
    bl_idname = "bim.edit_work_schedule"
    bl_label = "Edit Work Schedule"

    def execute(self, context):
        props = context.scene.BIMWorkScheduleProperties
        attributes = {}
        for attribute in props.work_schedule_attributes:
            if attribute.is_null:
                attributes[attribute.name] = None
            else:
                if attribute.data_type == "string":
                    attributes[attribute.name] = attribute.string_value
                elif attribute.data_type == "enum":
                    attributes[attribute.name] = attribute.enum_value
        self.file = IfcStore.get_file()
        ifcopenshell.api.run(
            "sequence.edit_work_schedule",
            self.file,
            **{"work_schedule": self.file.by_id(props.active_work_schedule_id), "attributes": attributes},
        )
        Data.load(IfcStore.get_file())
        bpy.ops.bim.disable_editing_work_schedule()
        return {"FINISHED"}


class RemoveWorkSchedule(bpy.types.Operator):
    bl_idname = "bim.remove_work_schedule"
    bl_label = "Remove Work Schedule"
    work_schedule: bpy.props.IntProperty()

    def execute(self, context):
        self.file = IfcStore.get_file()
        ifcopenshell.api.run(
            "sequence.remove_work_schedule", self.file, work_schedule=self.file.by_id(self.work_schedule)
        )
        Data.load(self.file)
        return {"FINISHED"}


class EnableEditingWorkSchedule(bpy.types.Operator):
    bl_idname = "bim.enable_editing_work_schedule"
    bl_label = "Enable Editing Work Schedule"
    work_schedule: bpy.props.IntProperty()

    def execute(self, context):
        self.props = context.scene.BIMWorkScheduleProperties
        self.props.active_work_schedule_id = self.work_schedule
        while len(self.props.work_schedule_attributes) > 0:
            self.props.work_schedule_attributes.remove(0)
        self.enable_editing_work_schedule()
        self.props.editing_type = "WORK_SCHEDULE"
        return {"FINISHED"}

    def enable_editing_work_schedule(self):
        data = Data.work_schedules[self.work_schedule]

        for attribute in IfcStore.get_schema().declaration_by_name("IfcWorkSchedule").all_attributes():
            data_type = ifcopenshell.util.attribute.get_primitive_type(attribute)
            if data_type == "entity":
                continue
            new = self.props.work_schedule_attributes.add()
            new.name = attribute.name()
            new.is_null = data[attribute.name()] is None
            new.is_optional = attribute.optional()
            new.data_type = data_type
            if attribute.name() in ["CreationDate", "StartTime", "FinishTime"]:
                new.string_value = "" if new.is_null else data[attribute.name()].isoformat()
            elif data_type == "string":
                new.string_value = "" if new.is_null else data[attribute.name()]
            elif data_type == "enum":
                new.enum_items = json.dumps(ifcopenshell.util.attribute.get_enum_items(attribute))
                if data[attribute.name()]:
                    new.enum_value = data[attribute.name()]


class EnableEditingTasks(bpy.types.Operator):
    bl_idname = "bim.enable_editing_tasks"
    bl_label = "Enable Editing Tasks"
    work_schedule: bpy.props.IntProperty()

    def execute(self, context):
        self.props = context.scene.BIMWorkScheduleProperties
        self.tprops = context.scene.BIMTaskTreeProperties
        self.props.active_work_schedule_id = self.work_schedule
        while len(self.tprops.tasks) > 0:
            self.tprops.tasks.remove(0)

        self.contracted_tasks = json.loads(self.props.contracted_tasks)
        for related_object_id in Data.work_schedules[self.work_schedule]["RelatedObjects"]:
            self.create_new_task_li(related_object_id, 0)
        bpy.ops.bim.load_task_properties()
        self.props.editing_type = "TASKS"
        return {"FINISHED"}

    def create_new_task_li(self, related_object_id, level_index):
        task = Data.tasks[related_object_id]
        new = self.tprops.tasks.add()
        new.ifc_definition_id = related_object_id
        new.is_expanded = related_object_id not in self.contracted_tasks
        new.level_index = level_index
        if task["RelatedObjects"]:
            new.has_children = True
            if new.is_expanded:
                for related_object_id in task["RelatedObjects"]:
                    self.create_new_task_li(related_object_id, level_index + 1)
        return {"FINISHED"}


class LoadTaskProperties(bpy.types.Operator):
    bl_idname = "bim.load_task_properties"
    bl_label = "Load Task Properties"
    task: bpy.props.IntProperty()

    def execute(self, context):
        self.props = context.scene.BIMWorkScheduleProperties
        self.tprops = context.scene.BIMTaskTreeProperties
        self.props.is_task_update_enabled = False
        for item in self.tprops.tasks:
            if self.task and item.ifc_definition_id != self.task:
                continue
            task = Data.tasks[item.ifc_definition_id]
            item.name = task["Name"] or "Unnamed"
            item.identification = task["Identification"] or "XXX"
            if self.props.active_task_id:
                item.is_predecessor = self.props.active_task_id in [
                    Data.sequences[r]["RelatedProcess"] for r in task["IsPredecessorTo"]
                ]
                item.is_successor = self.props.active_task_id in [
                    Data.sequences[r]["RelatingProcess"] for r in task["IsSuccessorFrom"]
                ]
            if task["TaskTime"]:
                task_time = Data.task_times[task["TaskTime"]]
                item.start = self.canonicalise_time(task_time["ScheduleStart"])
                item.finish = self.canonicalise_time(task_time["ScheduleFinish"])
                # TODO: duration
                item.duration = "-"
            else:
                item.start = "-"
                item.finish = "-"
                item.duration = "-"
        self.props.is_task_update_enabled = True
        return {"FINISHED"}

    def canonicalise_time(self, time):
        if not time:
            return "-"
        return time.strftime("%d/%m/%y")


class DisableEditingWorkSchedule(bpy.types.Operator):
    bl_idname = "bim.disable_editing_work_schedule"
    bl_label = "Disable Editing Work Schedule"

    def execute(self, context):
        context.scene.BIMWorkScheduleProperties.active_work_schedule_id = 0
        return {"FINISHED"}


class AddTask(bpy.types.Operator):
    bl_idname = "bim.add_task"
    bl_label = "Add Task"
    task: bpy.props.IntProperty()

    def execute(self, context):
        props = context.scene.BIMWorkScheduleProperties
        self.file = IfcStore.get_file()
        ifcopenshell.api.run("sequence.add_task", self.file, **{"parent_task": self.file.by_id(self.task)})
        Data.load(self.file)
        bpy.ops.bim.enable_editing_tasks(work_schedule=props.active_work_schedule_id)
        return {"FINISHED"}


class AddSummaryTask(bpy.types.Operator):
    bl_idname = "bim.add_summary_task"
    bl_label = "Add Task"
    work_schedule: bpy.props.IntProperty()

    def execute(self, context):
        props = context.scene.BIMWorkScheduleProperties
        self.file = IfcStore.get_file()
        ifcopenshell.api.run("sequence.add_task", self.file, **{"work_schedule": self.file.by_id(self.work_schedule)})
        Data.load(self.file)
        bpy.ops.bim.enable_editing_tasks(work_schedule=props.active_work_schedule_id)
        return {"FINISHED"}


class ExpandTask(bpy.types.Operator):
    bl_idname = "bim.expand_task"
    bl_label = "Expand Task"
    task: bpy.props.IntProperty()

    def execute(self, context):
        props = context.scene.BIMWorkScheduleProperties
        self.file = IfcStore.get_file()
        contracted_tasks = json.loads(props.contracted_tasks)
        contracted_tasks.remove(self.task)
        props.contracted_tasks = json.dumps(contracted_tasks)
        Data.load(self.file)
        bpy.ops.bim.enable_editing_tasks(work_schedule=props.active_work_schedule_id)
        return {"FINISHED"}


class ContractTask(bpy.types.Operator):
    bl_idname = "bim.contract_task"
    bl_label = "Contract Task"
    task: bpy.props.IntProperty()

    def execute(self, context):
        props = context.scene.BIMWorkScheduleProperties
        self.file = IfcStore.get_file()
        contracted_tasks = json.loads(props.contracted_tasks)
        contracted_tasks.append(self.task)
        props.contracted_tasks = json.dumps(contracted_tasks)
        Data.load(self.file)
        bpy.ops.bim.enable_editing_tasks(work_schedule=props.active_work_schedule_id)
        return {"FINISHED"}


class RemoveTask(bpy.types.Operator):
    bl_idname = "bim.remove_task"
    bl_label = "Remove Task"
    task: bpy.props.IntProperty()

    def execute(self, context):
        props = context.scene.BIMWorkScheduleProperties
        self.file = IfcStore.get_file()
        ifcopenshell.api.run(
            "sequence.remove_task",
            self.file,
            task=IfcStore.get_file().by_id(self.task),
        )
        Data.load(self.file)
        bpy.ops.bim.enable_editing_tasks(work_schedule=props.active_work_schedule_id)
        return {"FINISHED"}


class EnableEditingTaskTime(bpy.types.Operator):
    bl_idname = "bim.enable_editing_task_time"
    bl_label = "Enable Editing Task"
    task: bpy.props.IntProperty()

    def execute(self, context):
        props = context.scene.BIMWorkScheduleProperties
        self.file = IfcStore.get_file()

        task_time_id = Data.tasks[self.task]["TaskTime"] or self.add_task_time().id()

        while len(props.task_time_attributes) > 0:
            props.task_time_attributes.remove(0)

        data = Data.task_times[task_time_id]

        for attribute in IfcStore.get_schema().declaration_by_name("IfcTaskTime").all_attributes():
            data_type = ifcopenshell.util.attribute.get_primitive_type(attribute)
            if data_type == "entity":
                continue
            new = props.task_time_attributes.add()
            new.name = attribute.name()
            new.is_null = data[attribute.name()] is None
            new.is_optional = attribute.optional()
            new.data_type = data_type
            if data_type == "string":
                if isinstance(data[attribute.name()], datetime):
                    new.string_value = "" if new.is_null else data[attribute.name()].isoformat()
                else:
                    new.string_value = "" if new.is_null else data[attribute.name()]
            elif data_type == "boolean":
                new.bool_value = False if new.is_null else data[attribute.name()]
            elif data_type == "float":
                new.float_value = 0.0 if new.is_null else data[attribute.name()]
            elif data_type == "enum":
                new.enum_items = json.dumps(ifcopenshell.util.attribute.get_enum_items(attribute))
                if data[attribute.name()]:
                    new.enum_value = data[attribute.name()]
        props.active_task_time_id = task_time_id
        props.active_task_id = self.task
        props.editing_task_type = "TASKTIME"
        return {"FINISHED"}

    def add_task_time(self):
        task_time = ifcopenshell.api.run("sequence.add_task_time", self.file, task=self.file.by_id(self.task))
        Data.load(IfcStore.get_file())
        return task_time


class EditTaskTime(bpy.types.Operator):
    bl_idname = "bim.edit_task_time"
    bl_label = "Edit Task Time"

    def execute(self, context):
        props = context.scene.BIMWorkScheduleProperties
        attributes = {}
        for attribute in props.task_time_attributes:
            if attribute.is_null:
                attributes[attribute.name] = None
            else:
                if attribute.data_type == "string":
                    attributes[attribute.name] = attribute.string_value
                elif attribute.data_type == "boolean":
                    attributes[attribute.name] = attribute.bool_value
                elif attribute.data_type == "float":
                    attributes[attribute.name] = attribute.float_value
                elif attribute.data_type == "enum":
                    attributes[attribute.name] = attribute.enum_value

        attributes = self.convert_strings_to_date_times(attributes)

        self.file = IfcStore.get_file()
        ifcopenshell.api.run(
            "sequence.edit_task_time",
            self.file,
            **{"task_time": self.file.by_id(props.active_task_time_id), "attributes": attributes},
        )
        Data.load(IfcStore.get_file())
        bpy.ops.bim.disable_editing_task_time()
        bpy.ops.bim.load_task_properties(task=props.active_task_id)
        return {"FINISHED"}

    def convert_strings_to_date_times(self, attributes):
        for key, value in attributes.items():
            if not value:
                continue
            if "Start" in key or "Finish" in key or key == "StatusTime":
                try:
                    attributes[key] = parser.isoparse(value)
                except:
                    try:
                        attributes[key] = parser.parse(value, dayfirst=True, fuzzy=True)
                    except:
                        attributes[key] = None
        return attributes


class EnableEditingTask(bpy.types.Operator):
    bl_idname = "bim.enable_editing_task"
    bl_label = "Enable Editing Task"
    task: bpy.props.IntProperty()

    def execute(self, context):
        props = context.scene.BIMWorkScheduleProperties
        while len(props.task_attributes) > 0:
            props.task_attributes.remove(0)

        data = Data.tasks[self.task]

        for attribute in IfcStore.get_schema().declaration_by_name("IfcTask").all_attributes():
            data_type = ifcopenshell.util.attribute.get_primitive_type(attribute)
            if data_type == "entity":
                continue
            new = props.task_attributes.add()
            new.name = attribute.name()
            new.is_null = data[attribute.name()] is None
            new.is_optional = attribute.optional()
            new.data_type = data_type
            if data_type == "string":
                new.string_value = "" if new.is_null else data[attribute.name()]
            elif data_type == "boolean":
                new.bool_value = False if new.is_null else data[attribute.name()]
            elif data_type == "integer":
                new.int_value = 0 if new.is_null else data[attribute.name()]
            elif data_type == "enum":
                new.enum_items = json.dumps(ifcopenshell.util.attribute.get_enum_items(attribute))
                if data[attribute.name()]:
                    new.enum_value = data[attribute.name()]
        props.active_task_id = self.task
        props.editing_task_type = "ATTRIBUTES"
        return {"FINISHED"}


class DisableEditingTask(bpy.types.Operator):
    bl_idname = "bim.disable_editing_task"
    bl_label = "Disable Editing Task"

    def execute(self, context):
        context.scene.BIMWorkScheduleProperties.active_task_id = 0
        context.scene.BIMWorkScheduleProperties.active_task_time_id = 0
        return {"FINISHED"}


class EditTask(bpy.types.Operator):
    bl_idname = "bim.edit_task"
    bl_label = "Edit Task"

    def execute(self, context):
        props = context.scene.BIMWorkScheduleProperties
        attributes = {}
        for attribute in props.task_attributes:
            if attribute.is_null:
                attributes[attribute.name] = None
            else:
                if attribute.data_type == "string":
                    attributes[attribute.name] = attribute.string_value
                elif attribute.data_type == "boolean":
                    attributes[attribute.name] = attribute.bool_value
                elif attribute.data_type == "integer":
                    attributes[attribute.name] = attribute.int_value
                elif attribute.data_type == "enum":
                    attributes[attribute.name] = attribute.enum_value
        self.file = IfcStore.get_file()
        ifcopenshell.api.run(
            "sequence.edit_task", self.file, **{"task": self.file.by_id(props.active_task_id), "attributes": attributes}
        )
        Data.load(IfcStore.get_file())
        bpy.ops.bim.disable_editing_task()
        bpy.ops.bim.load_task_properties(task=props.active_task_id)
        return {"FINISHED"}


class AssignPredecessor(bpy.types.Operator):
    bl_idname = "bim.assign_predecessor"
    bl_label = "Assign Predecessor"
    task: bpy.props.IntProperty()

    def execute(self, context):
        props = context.scene.BIMWorkScheduleProperties
        self.file = IfcStore.get_file()
        ifcopenshell.api.run(
            "sequence.assign_sequence",
            self.file,
            relating_process=IfcStore.get_file().by_id(self.task),
            related_process=IfcStore.get_file().by_id(props.active_task_id),
        )
        Data.load(self.file)
        bpy.ops.bim.load_task_properties(task=self.task)
        return {"FINISHED"}


class AssignSuccessor(bpy.types.Operator):
    bl_idname = "bim.assign_successor"
    bl_label = "Assign Successor"
    task: bpy.props.IntProperty()

    def execute(self, context):
        props = context.scene.BIMWorkScheduleProperties
        self.file = IfcStore.get_file()
        ifcopenshell.api.run(
            "sequence.assign_sequence",
            self.file,
            relating_process=IfcStore.get_file().by_id(props.active_task_id),
            related_process=IfcStore.get_file().by_id(self.task),
        )
        Data.load(self.file)
        bpy.ops.bim.load_task_properties(task=self.task)
        return {"FINISHED"}


class UnassignPredecessor(bpy.types.Operator):
    bl_idname = "bim.unassign_predecessor"
    bl_label = "Unassign Predecessor"
    task: bpy.props.IntProperty()

    def execute(self, context):
        props = context.scene.BIMWorkScheduleProperties
        self.file = IfcStore.get_file()
        ifcopenshell.api.run(
            "sequence.unassign_sequence",
            self.file,
            relating_process=IfcStore.get_file().by_id(self.task),
            related_process=IfcStore.get_file().by_id(props.active_task_id),
        )
        Data.load(self.file)
        bpy.ops.bim.load_task_properties(task=self.task)
        return {"FINISHED"}


class UnassignSuccessor(bpy.types.Operator):
    bl_idname = "bim.unassign_successor"
    bl_label = "Unassign Successor"
    task: bpy.props.IntProperty()

    def execute(self, context):
        props = context.scene.BIMWorkScheduleProperties
        self.file = IfcStore.get_file()
        ifcopenshell.api.run(
            "sequence.unassign_sequence",
            self.file,
            relating_process=self.file.by_id(props.active_task_id),
            related_process=self.file.by_id(self.task),
        )
        Data.load(self.file)
        bpy.ops.bim.load_task_properties(task=self.task)
        return {"FINISHED"}


class AssignProduct(bpy.types.Operator):
    bl_idname = "bim.assign_product"
    bl_label = "Assign Product"
    task: bpy.props.IntProperty()
    related_product: bpy.props.StringProperty()

    def execute(self, context):
        related_products = (
            [bpy.data.objects.get(self.related_product)] if self.related_product else bpy.context.selected_objects
        )
        for related_product in related_products:
            self.file = IfcStore.get_file()
            ifcopenshell.api.run(
                "sequence.assign_product",
                self.file,
                relating_product=self.file.by_id(related_product.BIMObjectProperties.ifc_definition_id),
                related_object=self.file.by_id(self.task),
            )
        Data.load(self.file)
        return {"FINISHED"}


class UnassignProduct(bpy.types.Operator):
    bl_idname = "bim.unassign_product"
    bl_label = "Unassign Product"
    task: bpy.props.IntProperty()
    related_product: bpy.props.StringProperty()

    def execute(self, context):
        related_products = (
            [bpy.data.objects.get(self.related_product)] if self.related_product else bpy.context.selected_objects
        )
        for related_product in related_products:
            self.file = IfcStore.get_file()
            ifcopenshell.api.run(
                "sequence.unassign_product",
                self.file,
                relating_product=self.file.by_id(related_product.BIMObjectProperties.ifc_definition_id),
                related_object=self.file.by_id(self.task),
            )
        Data.load(self.file)
        return {"FINISHED"}


class GenerateGanttChart(bpy.types.Operator):
    bl_idname = "bim.generate_gantt_chart"
    bl_label = "Generate Gantt Chart"
    work_schedule: bpy.props.IntProperty()

    def execute(self, context):
        self.file = IfcStore.get_file()
        self.json = []
        for task_id in Data.work_schedules[self.work_schedule]["RelatedObjects"]:
            self.create_new_task_json(task_id)
        with open(os.path.join(bpy.context.scene.BIMProperties.data_dir, "gantt", "index.html"), "w") as f:
            with open(os.path.join(bpy.context.scene.BIMProperties.data_dir, "gantt", "index.mustache"), "r") as t:
                f.write(pystache.render(t.read(), {"json_data": json.dumps(self.json)}))
        webbrowser.open("file://" + os.path.join(bpy.context.scene.BIMProperties.data_dir, "gantt", "index.html"))
        return {"FINISHED"}

    def create_new_task_json(self, task_id):
        task = self.file.by_id(task_id)
        self.json.append(
            {
                "pID": task.id(),
                "pName": task.Name,
                "pStart": task.TaskTime.ScheduleStart if task.TaskTime else "",
                "pEnd": task.TaskTime.ScheduleFinish if task.TaskTime else "",
                "pPlanStart": task.TaskTime.ScheduleStart if task.TaskTime else "",
                "pPlanEnd": task.TaskTime.ScheduleFinish if task.TaskTime else "",
                "pClass": "ggroupblack",
                "pMile": 1 if task.IsMilestone else 0,
                "pComp": 0,
                "pGroup": 1,
                "pParent": task.Nests[0].RelatingObject.id() if task.Nests else 0,
                "pOpen": 1,
                "pCost": 1,
            }
        )
        for task_id in Data.tasks[task_id]["RelatedObjects"]:
            self.create_new_task_json(task_id)


class AddWorkCalendar(bpy.types.Operator):
    bl_idname = "bim.add_work_calendar"
    bl_label = "Add Work Calendar"

    def execute(self, context):
        ifcopenshell.api.run("sequence.add_work_calendar", IfcStore.get_file())
        Data.load(IfcStore.get_file())
        return {"FINISHED"}


class EditWorkCalendar(bpy.types.Operator):
    bl_idname = "bim.edit_work_calendar"
    bl_label = "Edit Work Calendar"

    def execute(self, context):
        props = context.scene.BIMWorkCalendarProperties
        attributes = {}
        for attribute in props.work_calendar_attributes:
            if attribute.is_null:
                attributes[attribute.name] = None
            else:
                if attribute.data_type == "string":
                    attributes[attribute.name] = attribute.string_value
                elif attribute.data_type == "enum":
                    attributes[attribute.name] = attribute.enum_value
        self.file = IfcStore.get_file()
        ifcopenshell.api.run(
            "sequence.edit_work_calendar",
            self.file,
            **{"work_calendar": self.file.by_id(props.active_work_calendar_id), "attributes": attributes},
        )
        Data.load(IfcStore.get_file())
        bpy.ops.bim.disable_editing_work_calendar()
        return {"FINISHED"}


class RemoveWorkCalendar(bpy.types.Operator):
    bl_idname = "bim.remove_work_calendar"
    bl_label = "Remove Work Plan"
    work_calendar: bpy.props.IntProperty()

    def execute(self, context):
        self.file = IfcStore.get_file()
        ifcopenshell.api.run(
            "sequence.remove_work_calendar", self.file, **{"work_calendar": self.file.by_id(self.work_calendar)}
        )
        Data.load(self.file)
        return {"FINISHED"}


class EnableEditingWorkCalendar(bpy.types.Operator):
    bl_idname = "bim.enable_editing_work_calendar"
    bl_label = "Enable Editing Work Calendar"
    work_calendar: bpy.props.IntProperty()

    def execute(self, context):
        self.props = context.scene.BIMWorkCalendarProperties
        while len(self.props.work_calendar_attributes) > 0:
            self.props.work_calendar_attributes.remove(0)

        data = Data.work_calendars[self.work_calendar]

        for attribute in IfcStore.get_schema().declaration_by_name("IfcWorkCalendar").all_attributes():
            data_type = ifcopenshell.util.attribute.get_primitive_type(attribute)
            if data_type == "entity":
                continue
            new = self.props.work_calendar_attributes.add()
            new.name = attribute.name()
            new.is_null = data[attribute.name()] is None
            new.is_optional = attribute.optional()
            new.data_type = data_type
            if data_type == "string":
                new.string_value = "" if new.is_null else data[attribute.name()]
            elif data_type == "enum":
                new.enum_items = json.dumps(ifcopenshell.util.attribute.get_enum_items(attribute))
                if data[attribute.name()]:
                    new.enum_value = data[attribute.name()]
        self.props.active_work_calendar_id = self.work_calendar
        self.props.editing_type = "ATTRIBUTES"
        return {"FINISHED"}


class DisableEditingWorkCalendar(bpy.types.Operator):
    bl_idname = "bim.disable_editing_work_calendar"
    bl_label = "Disable Editing Work Calendar"

    def execute(self, context):
        context.scene.BIMWorkCalendarProperties.active_work_calendar_id = 0
        return {"FINISHED"}


class ImportP6(bpy.types.Operator, ImportHelper):
    bl_idname = "import_p6.bim"
    bl_label = "Import P6"
    filename_ext = ".xml"
    filter_glob: bpy.props.StringProperty(default="*.xml", options={"HIDDEN"})

    def execute(self, context):
        from ifcp6.p62ifc import P62Ifc

        self.file = IfcStore.get_file()
        start = time.time()
        p62ifc = P62Ifc()
        p62ifc.xml = self.filepath
        p62ifc.file = self.file
        p62ifc.work_plan = self.file.by_type("IfcWorkPlan")[0]
        p62ifc.execute()
        Data.load(IfcStore.get_file())
        print("Import finished in {:.2f} seconds".format(time.time() - start))
        return {"FINISHED"}


class EnableEditingWorkCalendarTimes(bpy.types.Operator):
    bl_idname = "bim.enable_editing_work_calendar_times"
    bl_label = "Enable Editing Work Calendar Times"
    work_calendar: bpy.props.IntProperty()

    def execute(self, context):
        props = context.scene.BIMWorkCalendarProperties
        props.active_work_calendar_id = self.work_calendar
        props.editing_type = "WORKTIMES"
        return {"FINISHED"}


class AddWorkTime(bpy.types.Operator):
    bl_idname = "bim.add_work_time"
    bl_label = "Add Work Time"
    work_calendar: bpy.props.IntProperty()
    time_type: bpy.props.StringProperty()

    def execute(self, context):
        self.file = IfcStore.get_file()
        ifcopenshell.api.run(
            "sequence.add_work_time",
            self.file,
            **{"work_calendar": self.file.by_id(self.work_calendar), "time_type": self.time_type},
        )
        Data.load(IfcStore.get_file())
        return {"FINISHED"}


class EnableEditingWorkTime(bpy.types.Operator):
    bl_idname = "bim.enable_editing_work_time"
    bl_label = "Enable Editing Work Time"
    work_time: bpy.props.IntProperty()

    def execute(self, context):
        self.props = context.scene.BIMWorkCalendarProperties
        while len(self.props.work_time_attributes) > 0:
            self.props.work_time_attributes.remove(0)

        data = Data.work_times[self.work_time]

        for attribute in IfcStore.get_schema().declaration_by_name("IfcWorkTime").all_attributes():
            data_type = ifcopenshell.util.attribute.get_primitive_type(attribute)
            if data_type == "entity":
                continue
            new = self.props.work_time_attributes.add()
            new.name = attribute.name()
            new.is_null = data[attribute.name()] is None
            new.is_optional = attribute.optional()
            new.data_type = data_type
            if attribute.name() in ["Start", "Finish"]:
                new.string_value = "" if new.is_null else data[attribute.name()].isoformat()
            elif data_type == "string":
                new.string_value = "" if new.is_null else data[attribute.name()]
            elif data_type == "enum":
                new.enum_items = json.dumps(ifcopenshell.util.attribute.get_enum_items(attribute))
                if data[attribute.name()]:
                    new.enum_value = data[attribute.name()]

        self.initialise_recurrence_components()
        self.load_recurrence_pattern_data(data)
        self.props.active_work_time_id = self.work_time
        return {"FINISHED"}

    def initialise_recurrence_components(self):
        if len(self.props.day_components) == 0:
            for i in range(0, 31):
                new = self.props.day_components.add()
                new.name = str(i + 1)
        if len(self.props.weekday_components) == 0:
            for d in ["M", "T", "W", "T", "F", "S", "S"]:
                new = self.props.weekday_components.add()
                new.name = d
        if len(self.props.month_components) == 0:
            for m in ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]:
                new = self.props.month_components.add()
                new.name = m

    def load_recurrence_pattern_data(self, work_time):
        self.props.position = 0
        self.props.interval = 0
        self.props.occurrences = 0
        self.props.start_time = ""
        self.props.end_time = ""
        for component in self.props.day_components:
            component.is_specified = False
        for component in self.props.weekday_components:
            component.is_specified = False
        for component in self.props.month_components:
            component.is_specified = False
        if not work_time["RecurrencePattern"]:
            return
        recurrence_pattern = Data.recurrence_patterns[work_time["RecurrencePattern"]]
        for attribute in ["Position", "Interval", "Occurrences"]:
            if recurrence_pattern[attribute]:
                setattr(self.props, attribute.lower(), recurrence_pattern[attribute])
        for component in recurrence_pattern["DayComponent"] or []:
            self.props.day_components[component - 1].is_specified = True
        for component in recurrence_pattern["WeekdayComponent"] or []:
            self.props.weekday_components[component - 1].is_specified = True
        for component in recurrence_pattern["MonthComponent"] or []:
            self.props.month_components[component - 1].is_specified = True


class DisableEditingWorkTime(bpy.types.Operator):
    bl_idname = "bim.disable_editing_work_time"
    bl_label = "Disable Editing Work Time"

    def execute(self, context):
        context.scene.BIMWorkCalendarProperties.active_work_time_id = 0
        return {"FINISHED"}


class EditWorkTime(bpy.types.Operator):
    bl_idname = "bim.edit_work_time"
    bl_label = "Edit Work Time"

    def execute(self, context):
        self.props = context.scene.BIMWorkCalendarProperties
        attributes = {}
        for attribute in self.props.work_time_attributes:
            if attribute.is_null:
                attributes[attribute.name] = None
            else:
                if attribute.data_type == "string":
                    attributes[attribute.name] = attribute.string_value
                elif attribute.data_type == "enum":
                    attributes[attribute.name] = attribute.enum_value
        self.file = IfcStore.get_file()
        ifcopenshell.api.run(
            "sequence.edit_work_time",
            self.file,
            **{"work_time": self.file.by_id(self.props.active_work_time_id), "attributes": attributes},
        )

        work_time = Data.work_times[self.props.active_work_time_id]
        if work_time["RecurrencePattern"]:
            self.edit_recurrence_pattern(work_time["RecurrencePattern"])

        Data.load(IfcStore.get_file())
        bpy.ops.bim.disable_editing_work_time()
        return {"FINISHED"}

    def edit_recurrence_pattern(self, recurrence_pattern_id):
        recurrence_pattern = self.file.by_id(recurrence_pattern_id)
        attributes = {
            "Interval": self.props.interval if self.props.interval > 0 else None,
            "Occurrences": self.props.occurrences if self.props.occurrences > 0 else None,
        }
        applicable_data = {
            "DAILY": ["Interval", "Occurrences"],
            "WEEKLY": ["WeekdayComponent", "Interval", "Occurrences"],
            "MONTHLY_BY_DAY_OF_MONTH": ["DayComponent", "Interval", "Occurrences"],
            "MONTHLY_BY_POSITION": ["WeekdayComponent", "Position", "Interval", "Occurrences"],
            "BY_DAY_COUNT": ["Interval", "Occurrences"],
            "BY_WEEKDAY_COUNT": ["WeekdayComponent", "Interval", "Occurrences"],
            "YEARLY_BY_DAY_OF_MONTH": ["DayComponent", "MonthComponent", "Interval", "Occurrences"],
            "YEARLY_BY_POSITION": ["WeekdayComponent", "MonthComponent", "Position", "Interval", "Occurrences"],
        }
        if "Position" in applicable_data[recurrence_pattern.RecurrenceType]:
            attributes["Position"] = self.props.position if self.props.position != 0 else None
        if "DayComponent" in applicable_data[recurrence_pattern.RecurrenceType]:
            attributes["DayComponent"] = [i + 1 for i, c in enumerate(self.props.day_components) if c.is_specified]
        if "WeekdayComponent" in applicable_data[recurrence_pattern.RecurrenceType]:
            attributes["WeekdayComponent"] = [
                i + 1 for i, c in enumerate(self.props.weekday_components) if c.is_specified
            ]
        if "MonthComponent" in applicable_data[recurrence_pattern.RecurrenceType]:
            attributes["MonthComponent"] = [i + 1 for i, c in enumerate(self.props.month_components) if c.is_specified]
        ifcopenshell.api.run(
            "sequence.edit_recurrence_pattern",
            self.file,
            **{"recurrence_pattern": recurrence_pattern, "attributes": attributes},
        )


class RemoveWorkTime(bpy.types.Operator):
    bl_idname = "bim.remove_work_time"
    bl_label = "Remove Work Plan"
    work_time: bpy.props.IntProperty()

    def execute(self, context):
        self.file = IfcStore.get_file()
        ifcopenshell.api.run("sequence.remove_work_time", self.file, **{"work_time": self.file.by_id(self.work_time)})
        Data.load(self.file)
        return {"FINISHED"}


class AssignRecurrencePattern(bpy.types.Operator):
    bl_idname = "bim.assign_recurrence_pattern"
    bl_label = "Assign Recurrence Pattern"
    work_time: bpy.props.IntProperty()
    recurrence_type: bpy.props.StringProperty()

    def execute(self, context):
        self.file = IfcStore.get_file()
        ifcopenshell.api.run(
            "sequence.assign_recurrence_pattern",
            self.file,
            **{"parent": self.file.by_id(self.work_time), "recurrence_type": self.recurrence_type},
        )
        Data.load(IfcStore.get_file())
        return {"FINISHED"}


class UnassignRecurrencePattern(bpy.types.Operator):
    bl_idname = "bim.unassign_recurrence_pattern"
    bl_label = "Unassign Recurrence Pattern"
    recurrence_pattern: bpy.props.IntProperty()

    def execute(self, context):
        self.file = IfcStore.get_file()
        ifcopenshell.api.run(
            "sequence.unassign_recurrence_pattern",
            self.file,
            **{"recurrence_pattern": self.file.by_id(self.recurrence_pattern)},
        )
        Data.load(self.file)
        return {"FINISHED"}


class AddTimePeriod(bpy.types.Operator):
    bl_idname = "bim.add_time_period"
    bl_label = "Add Time Period"
    recurrence_pattern: bpy.props.IntProperty()

    def execute(self, context):
        self.props = context.scene.BIMWorkCalendarProperties
        self.file = IfcStore.get_file()
        try:
            start_time = parser.parse(self.props.start_time)
            end_time = parser.parse(self.props.end_time)
        except:
            return {"FINISHED"}
        ifcopenshell.api.run(
            "sequence.add_time_period",
            self.file,
            **{
                "recurrence_pattern": self.file.by_id(self.recurrence_pattern),
                "start_time": start_time,
                "end_time": end_time,
            },
        )
        self.props.start_time = ""
        self.props.end_time = ""
        Data.load(IfcStore.get_file())
        return {"FINISHED"}


class RemoveTimePeriod(bpy.types.Operator):
    bl_idname = "bim.remove_time_period"
    bl_label = "Remove Time Period"
    time_period: bpy.props.IntProperty()

    def execute(self, context):
        self.file = IfcStore.get_file()
        ifcopenshell.api.run(
            "sequence.remove_time_period",
            self.file,
            **{"time_period": self.file.by_id(self.time_period)},
        )
        Data.load(self.file)
        return {"FINISHED"}


class EnableEditingTaskCalendar(bpy.types.Operator):
    bl_idname = "bim.enable_editing_task_calendar"
    bl_label = "Enable Editing Task Calendar"
    task: bpy.props.IntProperty()

    def execute(self, context):
        props = context.scene.BIMWorkScheduleProperties
        props.active_task_id = self.task
        props.editing_task_type = "CALENDAR"
        return {"FINISHED"}


class EditTaskCalendar(bpy.types.Operator):
    bl_idname = "bim.edit_task_calendar"
    bl_label = "Edit Task Calendar"
    work_calendar: bpy.props.IntProperty()
    task: bpy.props.IntProperty()

    def execute(self, context):
        self.file = IfcStore.get_file()
        ifcopenshell.api.run(
            "control.assign_control",
            self.file,
            **{
                "relating_control": self.file.by_id(self.work_calendar),
                "related_object": self.file.by_id(self.task),
            },
        )
        Data.load(IfcStore.get_file())
        return {"FINISHED"}


class RemoveTaskCalendar(bpy.types.Operator):
    bl_idname = "bim.remove_task_calendar"
    bl_label = "Remove Task Calendar"
    work_calendar: bpy.props.IntProperty()
    task: bpy.props.IntProperty()

    def execute(self, context):
        self.file = IfcStore.get_file()
        ifcopenshell.api.run(
            "control.unassign_control",
            self.file,
            **{
                "relating_control": self.file.by_id(self.work_calendar),
                "related_object": self.file.by_id(self.task),
            },
        )
        Data.load(IfcStore.get_file())
        return {"FINISHED"}


class EnableEditingTaskSequence(bpy.types.Operator):
    bl_idname = "bim.enable_editing_task_sequence"
    bl_label = "Enable Editing Task Sequence"
    task: bpy.props.IntProperty()

    def execute(self, context):
        props = context.scene.BIMWorkScheduleProperties
        props.active_task_id = self.task
        props.editing_task_type = "SEQUENCE"
        bpy.ops.bim.load_task_properties()
        return {"FINISHED"}


class DisableEditingTaskTime(bpy.types.Operator):
    bl_idname = "bim.disable_editing_task_time"
    bl_label = "Disable Editing Task Time"

    def execute(self, context):
        context.scene.BIMWorkScheduleProperties.active_task_time_id = 0
        bpy.ops.bim.disable_editing_task()
        return {"FINISHED"}
