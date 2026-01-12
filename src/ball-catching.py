import time
import mujoco
import mujoco.viewer
import utils

model = mujoco.MjModel.from_xml_path("robohand.xml")
data = mujoco.MjData(model)

palm_adr = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SENSOR, "touch_hand")
goal_sensors = [
        mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SENSOR, "finger1_t"),
        mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SENSOR, "finger2_t"),
        mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SENSOR, "finger3_t"),
        mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SENSOR, "tip_f5"),
    ]
finger_act_ids = [
    mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in [
         "finger11", "finger12", "finger13",
         "finger21", "finger22", "finger23",
         "finger31", "finger32", "finger33",
         "finger41", "finger42", "finger43",
         "finger51", "finger52",
        ]
    ]
ball_vadr = model.jnt_dofadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")]

ball_speed = 0.1 
touch_threshold = 1e-3  
close_u = 0.0 
close_u_max = 0.05  
ramp_rate = 0.001  

touched = [False] * len(goal_sensors)  
state = "approach"  

with mujoco.viewer.launch_passive(model, data) as viewer:
        utils.look_at_the_hand(viewer)
        while viewer.is_running():
            dt_sim = model.opt.timestep  

            if state == "approach":
               
                for aid in finger_act_ids:
                    data.ctrl[aid] = 0.0  
                data.qvel[ball_vadr] = ball_speed

                if data.sensordata[palm_adr] > touch_threshold:
                    data.qvel[ball_vadr] = 0.0  
                    state = "close"
                    close_u = 0.0
                    touched = [False] * len(goal_sensors) 

            elif state == "close":
    
                data.qvel[ball_vadr] = 0.0  
                for i, adr in enumerate(goal_sensors):
                    if not touched[i] and data.sensordata[adr] > touch_threshold:
                        touched[i] = True  
                close_u = min(close_u + ramp_rate * dt_sim, close_u_max)
                for aid in finger_act_ids:
                    data.ctrl[aid] = close_u 
                if all(touched):
                    state = "hold"

            elif state == "hold":
              
                data.qvel[ball_vadr] = 0.0
                for aid in finger_act_ids:
                    data.ctrl[aid] = 0.0

            mujoco.mj_step(model, data) 

            viewer.sync()  
