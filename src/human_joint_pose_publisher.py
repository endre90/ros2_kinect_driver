import sys
import rclpy
import time
from pykinect2 import PyKinectV2
from pykinect2.PyKinectV2 import __all__
from pykinect2 import PyKinectRuntime
from pykinect2.PyKinectRuntime import KinectBody as knb
#from geometry_msgs.msg import Point
from unification_ros2_messages.msg import HumanJoints
from unification_ros2_messages.msg import JointPosition
from unification_ros2_messages.msg import KinectHumans
from unification_ros2_messages.msg import Gestures
import ctypes
import datetime
from ctypes import *
import pygame
import sys
import comtypes
from comtypes import *
import time
import numpy

if sys.hexversion >= 0x03000000:
    import _thread as thread
else:
    import thread

# colors for drawing different bodies
SKELETON_COLORS = [pygame.color.THECOLORS["red"], 
                  pygame.color.THECOLORS["blue"], 
                  pygame.color.THECOLORS["green"], 
                  pygame.color.THECOLORS["orange"], 
                  pygame.color.THECOLORS["purple"], 
                  pygame.color.THECOLORS["yellow"], 
                  pygame.color.THECOLORS["violet"]]
pid = 0

#f = open( 'C:\\Users\\lab_pc\\Desktop\\PyDataBody.txt', "a")
jointlist = ["SpineBase",
             "SpineMid",
			"Neck",
			"Head",
			"ShoulderLeft",
			"ElbowLeft",
			"WristLeft",
			"HandLeft",
			"ShoulderRight",
			"ElbowRight",
			"WristRight",
			"HandRight",
			"HipLeft",
			"KneeLeft",
			"AnkleLeft",
			"FootLeft",
			"HipRight",
			"KneeRight",
			"AnkleRight",
			"FootRight",
			"SpineShoulder",
			"HandTipLeft",
			"ThumbLeft",
			"HandTipRight",
			"ThumbRight" ]

class BodyGameRuntime(object):

    def __init__(self, args=None):

        pygame.init()

        rclpy.init(args=args)

        # ROS2 part
        self.node = rclpy.create_node('human_joint_pose_publisher')
        self.timer_period_2 = 0.3
        self.pub1 = self.node.create_publisher(KinectHumans, 'kinect_humans')
        self.pub2 = self.node.create_publisher(Gestures, 'gestures')
        #self.pub2 = self.node.create_publisher(Point, 'kinect_joints')

        # Used to manage how fast the screen updates
        self._clock = pygame.time.Clock()

        # Set the width and height of the screen [width, height]
        self._infoObject = pygame.display.Info()
        self._screen = pygame.display.set_mode((self._infoObject.current_w >> 1, self._infoObject.current_h >> 1), 
                                               pygame.HWSURFACE|pygame.DOUBLEBUF|pygame.RESIZABLE, 32)

        pygame.display.set_caption("Kinect for Windows v2 Body Game")

        # Loop until the user clicks the close button.
        self._done = False

        # Used to manage how fast the screen updates
        self._clock = pygame.time.Clock()

        # Kinect runtime object, we want only color and body frames 
        self._kinect = PyKinectRuntime.PyKinectRuntime(PyKinectV2.FrameSourceTypes_Color | PyKinectV2.FrameSourceTypes_Body)
        #self.lh = PyKinectRuntime.KinectBody(PyKinectRuntime.get_last_body_frame())

        # back buffer surface for getting Kinect color frames, 32bit color, width and height equal to the Kinect color frame size
        self._frame_surface = pygame.Surface((self._kinect.color_frame_desc.Width, self._kinect.color_frame_desc.Height), 0, 32)

        # here we will store skeleton data 
        self._bodies = None

        # ROS2 part value inits:
        self.joint_name = ''
        self.joint_pose_x = -1
        self.joint_pose_y = -1
        self.joint_pose_z = -1
        self.human_id = -1

        # ROS2 spinner, constructor and destructor
        #rclpy.spin(self.node)
        #self.node.destroy_node()
        #rclpy.shutdown() 

    def draw_body_bone(self, joints, jointPoints, color, joint0, joint1):

        joint0State = joints[joint0].TrackingState;
        joint1State = joints[joint1].TrackingState;

        # both joints are not tracked
        if (joint0State == PyKinectV2.TrackingState_NotTracked) or (joint1State == PyKinectV2.TrackingState_NotTracked): 
            pass

        # any joints are not *really* tracked
        if (joint0State == PyKinectV2.TrackingState_Inferred) or (joint1State == PyKinectV2.TrackingState_Inferred):
            pass

        if (joint0State == PyKinectV2.TrackingState_Tracked) and (joint1State == PyKinectV2.TrackingState_Tracked):

        # both are measured
            start = (jointPoints[joint0].x, jointPoints[joint0].y)

            end = (jointPoints[joint1].x, jointPoints[joint1].y)

            try:
                pygame.draw.line(self._frame_surface, color, start, end, 8)

            except: # need to catch it due to possible invalid positions (with inf)
                pass

    def draw_body(self, joints, jointPoints, color):
        # Torso
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_Head, PyKinectV2.JointType_Neck);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_Neck, PyKinectV2.JointType_SpineShoulder);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_SpineShoulder, PyKinectV2.JointType_SpineMid);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_SpineMid, PyKinectV2.JointType_SpineBase);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_SpineShoulder, PyKinectV2.JointType_ShoulderRight);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_SpineShoulder, PyKinectV2.JointType_ShoulderLeft);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_SpineBase, PyKinectV2.JointType_HipRight);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_SpineBase, PyKinectV2.JointType_HipLeft);
        # print(joints[jointPoints])
        # Right Arm    
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_ShoulderRight, PyKinectV2.JointType_ElbowRight);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_ElbowRight, PyKinectV2.JointType_WristRight);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_WristRight, PyKinectV2.JointType_HandRight);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_HandRight, PyKinectV2.JointType_HandTipRight);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_WristRight, PyKinectV2.JointType_ThumbRight);

        # Left Arm
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_ShoulderLeft, PyKinectV2.JointType_ElbowLeft);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_ElbowLeft, PyKinectV2.JointType_WristLeft);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_WristLeft, PyKinectV2.JointType_HandLeft);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_HandLeft, PyKinectV2.JointType_HandTipLeft);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_WristLeft, PyKinectV2.JointType_ThumbLeft);

        # Right Leg
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_HipRight, PyKinectV2.JointType_KneeRight);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_KneeRight, PyKinectV2.JointType_AnkleRight);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_AnkleRight, PyKinectV2.JointType_FootRight);

        # Left Leg
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_HipLeft, PyKinectV2.JointType_KneeLeft);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_KneeLeft, PyKinectV2.JointType_AnkleLeft);
        self.draw_body_bone(joints, jointPoints, color, PyKinectV2.JointType_AnkleLeft, PyKinectV2.JointType_FootLeft);



    def draw_color_frame(self, frame, target_surface):
        target_surface.lock()
        address = self._kinect.surface_as_array(target_surface.get_buffer())
        ctypes.memmove(address, frame.ctypes.data, frame.size)
        del address
        target_surface.unlock()


    def run(self):

        gestures = Gestures()

        # -------- Main Program Loop -----------
        while not self._done:

            #hands = PyKinectRuntime.KinectBody
            #lh = hands.HandLeftState
            #print(lh)

            #print(self.lh.hand_left_state)

            #print(knb.hleft)

            # --- Main event loop
            for event in pygame.event.get(): # User did something
                if event.type == pygame.QUIT: # If user clicked close
                    self._done = True # Flag that we are done so we exit this loop

                elif event.type == pygame.VIDEORESIZE: # window resized
                    self._screen = pygame.display.set_mode(event.dict['size'], 
                                               pygame.HWSURFACE|pygame.DOUBLEBUF|pygame.RESIZABLE, 32)
                    
            # --- Game logic should go here

            # --- Getting frames and drawing  
            # --- Woohoo! We've got a color frame! Let's fill out back buffer surface with frame's data 
            if self._kinect.has_new_color_frame():
                frame = self._kinect.get_last_color_frame()
                self.draw_color_frame(frame, self._frame_surface)
                frame = None

            # --- Cool! We have a body frame, so can get skeletons
            if self._kinect.has_new_body_frame(): 
                self._bodies = self._kinect.get_last_body_frame()

            # --- draw skeletons to _frame_surface
            if self._bodies is not None:

                self.humans_list = []

                for i in range(0, self._kinect.max_body_count):

                    body = self._bodies.bodies[i]


                    if not body.is_tracked:
                        continue

                    joints = body.joints
                    left_hand = body.hand_left_state
                    right_hand = body.hand_right_state

                    if left_hand == 0:
                        left_hand_expl = "unknown"
                    elif left_hand == 1:
                        left_hand_expl = "not_tracked"
                    elif left_hand == 2:
                        left_hand_expl = "open"
                    elif left_hand == 3:
                        left_hand_expl = "closed"
                    elif left_hand == 4:
                        left_hand_expl = "lasso"

                    if right_hand == 0:
                        right_hand_expl = "unknown"
                    elif right_hand == 1:
                        right_hand_expl = "not_tracked"
                    elif right_hand == 2:
                        right_hand_expl = "open"
                    elif right_hand == 3:
                        right_hand_expl = "closed"
                    elif right_hand == 4:
                        right_hand_expl = "lasso"

                    gestures.human_id = i
                    gestures.left_hand = left_hand_expl
                    gestures.right_hand = right_hand_expl

                    
                    
                    #print(left_hand_expl, right_hand_expl)
                    # convert joint coordinates to color space
                    joint_points = self._kinect.body_joints_to_color_space(joints)
                    self.draw_body(joints, joint_points, SKELETON_COLORS[i])

                    self.human_joint_list = []

                    for j in range (0, PyKinectV2.JointType_Count):
                        if joints[j].TrackingState == 2:

                            #self.joint_detected = True
                            joint_position_msg = JointPosition()
                            joint_position_msg.joint_id = jointlist[j]
                            joint_position_msg.x = joints[j].Position.x
                            joint_position_msg.y = joints[j].Position.y
                            joint_position_msg.z = joints[j].Position.z
                            #print(jointlist[j])
                            
                            self.human_joint_list.append(joint_position_msg)
                            #print (self.human_joint_list)
                        
                        else:

                            pass

                    human_joints_msg = HumanJoints()
                    human_joints_msg.human_id = i
                    human_joints_msg.joint_list = self.human_joint_list
                    self.humans_list.append(human_joints_msg)

                kinect_humans_msg = KinectHumans()
                kinect_humans_msg.human_list = self.humans_list
                self.pub1.publish(kinect_humans_msg)
                self.pub2.publish(gestures)

                    #self.kinect_humans_list.append()

                            # print("\n", datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S.%f"))
                            # print(j, jointlist[j], "x", joints[j].Position.x, "y", joints[j].Position.y, "z", joints[j].Position.z, i)
                           

            # --- copy back buffer surface pixels to the screen, resize it if needed and keep aspect ratio
            # --- (screen size may be different from Kinect's color frame size) 
            h_to_w = float(self._frame_surface.get_height()) / self._frame_surface.get_width()
            target_height = int(h_to_w * self._screen.get_width())
            surface_to_draw = pygame.transform.scale(self._frame_surface, (self._screen.get_width(), target_height));
            self._screen.blit(surface_to_draw, (0,0))
            surface_to_draw = None
            pygame.display.update()

            # --- Go ahead and update the screen with what we've drawn.
            pygame.display.flip()

            # --- Limit to 60 frames per second
            self._clock.tick(60)

        # Close our Kinect sensor, close the window and quit.
        self._kinect.close()
        pygame.quit()

__main__ = "Kinect v2 Body Game"
game = BodyGameRuntime();
game.run();

