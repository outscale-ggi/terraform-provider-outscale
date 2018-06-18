package eim

import "time"

// CreatePolicyInput ...
type CreatePolicyInput struct {
	_              struct{} `type:"structure"`
	Description    *string  `type:"string"`
	Path           *string  `type:"string"`
	PolicyDocument *string  `min:"1" type:"string" required:"true"`
	PolicyName     *string  `min:"1" type:"string" required:"true"`
}

// CreatePolicyOutput ...
type CreatePolicyOutput struct {
	_      struct{} `type:"structure"`
	Policy *Policy  `type:"structure"`
}

// Policy ...
type Policy struct {
	_                struct{}   `type:"structure"`
	Arn              *string    `min:"20" type:"string"`
	AttachmentCount  *int64     `type:"integer"`
	CreateDate       *time.Time `type:"timestamp" timestampFormat:"iso8601"`
	DefaultVersionId *string    `type:"string"`
	Description      *string    `type:"string"`
	IsAttachable     *bool      `type:"boolean"`
	Path             *string    `type:"string"`
	PolicyId         *string    `min:"16" type:"string"`
	PolicyName       *string    `min:"1" type:"string"`
	UpdateDate       *time.Time `type:"timestamp" timestampFormat:"iso8601"`
}

// GetPolicyInput ...
type GetPolicyInput struct {
	_         struct{} `type:"structure"`
	PolicyArn *string  `min:"20" type:"string" required:"true"`
}

// GetPolicyOutput ...
type GetPolicyOutput struct {
	_         struct{} `type:"structure"`
	Policy    *Policy  `type:"structure"`
	RequestId *string  `type:"string"`
}

// GetPolicyVersionInput ...
type GetPolicyVersionInput struct {
	_         struct{} `type:"structure"`
	PolicyArn *string  `min:"20" type:"string" required:"true"`
	VersionId *string  `type:"string" required:"true"`
}

// GetPolicyVersionOutput ...
type GetPolicyVersionOutput struct {
	_             struct{}       `type:"structure"`
	PolicyVersion *PolicyVersion `type:"structure"`
}

// PolicyVersion ...
type PolicyVersion struct {
	_                struct{}   `type:"structure"`
	CreateDate       *time.Time `type:"timestamp" timestampFormat:"iso8601"`
	Document         *string    `min:"1" type:"string"`
	IsDefaultVersion *bool      `type:"boolean"`
	VersionId        *string    `type:"string"`
}

// DeletePolicyInput ...
type DeletePolicyInput struct {
	_         struct{} `type:"structure"`
	PolicyArn *string  `min:"20" type:"string" required:"true"`
}

// DeletePolicyOutput ...
type DeletePolicyOutput struct {
	_ struct{} `type:"structure"`
}

// DeletePolicyVersionInput ...
type DeletePolicyVersionInput struct {
	_         struct{} `type:"structure"`
	PolicyArn *string  `min:"20" type:"string" required:"true"`
	VersionId *string  `type:"string" required:"true"`
}

// DeletePolicyVersionOutput ...
type DeletePolicyVersionOutput struct {
	_ struct{} `type:"structure"`
}

// ListPolicyVersionsInput ...
type ListPolicyVersionsInput struct {
	_         struct{} `type:"structure"`
	Marker    *string  `min:"1" type:"string"`
	MaxItems  *int64   `min:"1" type:"integer"`
	PolicyArn *string  `min:"20" type:"string" required:"true"`
}

// ListPolicyVersionsOutput ...
type ListPolicyVersionsOutput struct {
	_           struct{}         `type:"structure"`
	IsTruncated *bool            `type:"boolean"`
	Marker      *string          `min:"1" type:"string"`
	Versions    []*PolicyVersion `type:"list"`
}

// CreateGroupInput ...
type CreateGroupInput struct {
	_         struct{} `type:"structure"`
	GroupName *string  `min:"1" type:"string" required:"true"`
	Path      *string  `min:"1" type:"string"`
}

// CreateGroupOutput ...
type CreateGroupOutput struct {
	_     struct{} `type:"structure"`
	Group *Group   `type:"structure" required:"true"`
}

// Group ...
type Group struct {
	_          struct{}   `type:"structure"`
	Arn        *string    `min:"20" type:"string" required:"true"`
	CreateDate *time.Time `type:"timestamp" timestampFormat:"iso8601" required:"true"`
	GroupId    *string    `min:"16" type:"string" required:"true"`
	GroupName  *string    `min:"1" type:"string" required:"true"`
	UserName   *string    `min:"1" type:"string" required:"true"`
	Path       *string    `min:"1" type:"string" required:"true"`
}

// GetGroupInput ...
type GetGroupInput struct {
	_         struct{} `type:"structure"`
	GroupName *string  `min:"1" type:"string" required:"true"`
	Marker    *string  `min:"1" type:"string"`
	MaxItems  *int64   `min:"1" type:"integer"`
}

// GetGroupOutput ...
type GetGroupOutput struct {
	_           struct{} `type:"structure"`
	Group       *Group   `type:"structure" required:"true"`
	IsTruncated *bool    `type:"boolean"`
	Marker      *string  `min:"1" type:"string"`
	Users       []*User  `type:"list" required:"true"`
}

// User ...
type User struct {
	_                struct{}   `type:"structure"`
	Arn              *string    `min:"20" type:"string" required:"true"`
	CreateDate       *time.Time `type:"timestamp" timestampFormat:"iso8601" required:"true"`
	PasswordLastUsed *time.Time `type:"timestamp" timestampFormat:"iso8601"`
	Path             *string    `min:"1" type:"string" required:"true"`
	UserId           *string    `min:"16" type:"string" required:"true"`
	UserName         *string    `min:"1" type:"string" required:"true"`
}

// UpdateGroupInput ...
type UpdateGroupInput struct {
	_            struct{} `type:"structure"`
	GroupName    *string  `min:"1" type:"string" required:"true"`
	NewGroupName *string  `min:"1" type:"string"`
	NewPath      *string  `min:"1" type:"string"`
}

// UpdateGroupOutput ...
type UpdateGroupOutput struct {
	_ struct{} `type:"structure"`
}

// DeleteGroupInput ...
type DeleteGroupInput struct {
	_         struct{} `type:"structure"`
	GroupName *string  `min:"1" type:"string" required:"true"`
}

// DeleteGroupOutput ...
type DeleteGroupOutput struct {
	_ struct{} `type:"structure"`
}

// AddUserToGroupInput ...
type AddUserToGroupInput struct {
	_         struct{} `type:"structure"`
	GroupName *string  `min:"1" type:"string" required:"true"`
	UserName  *string  `min:"1" type:"string" required:"true"`
}

// AddUserToGroupOutput ...
type AddUserToGroupOutput struct {
	_ struct{} `type:"structure"`
}

// RemoveUserFromGroupInput ...
type RemoveUserFromGroupInput struct {
	_         struct{} `type:"structure"`
	GroupName *string  `min:"1" type:"string" required:"true"`
	UserName  *string  `min:"1" type:"string" required:"true"`
}

// RemoveUserFromGroupOutput ...
type RemoveUserFromGroupOutput struct {
	_ struct{} `type:"structure"`
}

// CreateUserInput ...
type CreateUserInput struct {
	_        struct{} `type:"structure"`
	Path     *string  `min:"1" type:"string"`
	UserName *string  `min:"1" type:"string" required:"true"`
}

// CreateUserOutput ...
type CreateUserOutput struct {
	_    struct{} `type:"structure"`
	User *User    `type:"structure"`
}

// GetUserInput ...
type GetUserInput struct {
	_        struct{} `type:"structure"`
	UserName *string  `min:"1" type:"string"`
}

// GetUserOutput ...
type GetUserOutput struct {
	_    struct{} `type:"structure"`
	User *User    `type:"structure" required:"true"`
}

// UpdateUserInput ...
type UpdateUserInput struct {
	_           struct{} `type:"structure"`
	NewPath     *string  `min:"1" type:"string"`
	NewUserName *string  `min:"1" type:"string"`
	UserName    *string  `min:"1" type:"string" required:"true"`
}

// UpdateUserOutput ...
type UpdateUserOutput struct {
	_ struct{} `type:"structure"`
}

// ListGroupsForUserInput ...
type ListGroupsForUserInput struct {
	_        struct{} `type:"structure"`
	Marker   *string  `min:"1" type:"string"`
	MaxItems *int64   `min:"1" type:"integer"`
	UserName *string  `min:"1" type:"string" required:"true"`
}

// ListGroupsForUserOutput ...
type ListGroupsForUserOutput struct {
	_           struct{} `type:"structure"`
	Groups      []*Group `type:"list" required:"true"`
	IsTruncated *bool    `type:"boolean"`
	Marker      *string  `min:"1" type:"string"`
}

// DeleteUserInput ...
type DeleteUserInput struct {
	_        struct{} `type:"structure"`
	UserName *string  `min:"1" type:"string" required:"true"`
}

// DeleteUserOutput ...
type DeleteUserOutput struct {
	_ struct{} `type:"structure"`
}

// SetDefaultPolicyVersionInput ...
type SetDefaultPolicyVersionInput struct {
	_         struct{} `type:"structure"`
	PolicyArn *string  `min:"20" type:"string" required:"true"`
	VersionId *string  `type:"string" required:"true"`
}

// SetDefaultPolicyVersionOutput ...
type SetDefaultPolicyVersionOutput struct {
	_ struct{} `type:"structure"`
}

// AttachUserPolicyInput ...
type AttachUserPolicyInput struct {
	_         struct{} `type:"structure"`
	PolicyArn *string  `min:"20" type:"string" required:"true"`
	UserName  *string  `min:"1" type:"string" required:"true"`
}

// AttachUserPolicyOutput ...
type AttachUserPolicyOutput struct {
	_ struct{} `type:"structure"`
}

// ListAttachedUserPoliciesInput ...
type ListAttachedUserPoliciesInput struct {
	_          struct{} `type:"structure"`
	Marker     *string  `min:"1" type:"string"`
	MaxItems   *int64   `min:"1" type:"integer"`
	PathPrefix *string  `type:"string"`
	UserName   *string  `min:"1" type:"string" required:"true"`
}

// ListAttachedUserPoliciesOutput ...
type ListAttachedUserPoliciesOutput struct {
	_                struct{}          `type:"structure"`
	AttachedPolicies []*AttachedPolicy `type:"list"`
	IsTruncated      *bool             `type:"boolean"`
	Marker           *string           `min:"1" type:"string"`
}

// AttachedPolicy ...
type AttachedPolicy struct {
	_          struct{} `type:"structure"`
	PolicyArn  *string  `min:"20" type:"string"`
	PolicyName *string  `min:"1" type:"string"`
}

// DetachUserPolicyInput ...
type DetachUserPolicyInput struct {
	_         struct{} `type:"structure"`
	PolicyArn *string  `min:"20" type:"string" required:"true"`
	UserName  *string  `min:"1" type:"string" required:"true"`
}

// DetachUserPolicyOutput ...
type DetachUserPolicyOutput struct {
	_ struct{} `type:"structure"`
}

// GetUserPolicyInput ...
type GetUserPolicyInput struct {
	_          struct{} `type:"structure"`
	PolicyName *string  `min:"1" type:"string" required:"true"`
	UserName   *string  `min:"1" type:"string" required:"true"`
}

// GetUserPolicyOutput ...
type GetUserPolicyOutput struct {
	_              struct{} `type:"structure"`
	PolicyDocument *string  `min:"1" type:"string" required:"true"`
	PolicyName     *string  `min:"1" type:"string" required:"true"`
	UserName       *string  `min:"1" type:"string" required:"true"`
}

// ListUsersInput ...
type ListUsersInput struct {
	_          struct{} `type:"structure"`
	Marker     *string  `min:"1" type:"string"`
	MaxItems   *int64   `min:"1" type:"integer"`
	PathPrefix *string  `min:"1" type:"string"`
}

// ListUsersOutput ...
type ListUsersOutput struct {
	_           struct{} `type:"structure"`
	IsTruncated *bool    `type:"boolean"`
	Marker      *string  `min:"1" type:"string"`
	Users       []*User  `type:"list" required:"true"`
}

// ListGroupsInput ...
type ListGroupsInput struct {
	_          struct{} `type:"structure"`
	Marker     *string  `min:"1" type:"string"`
	MaxItems   *int64   `min:"1" type:"integer"`
	PathPrefix *string  `min:"1" type:"string"`
}

// ListGroupsOutput ...
type ListGroupsOutput struct {
	_           struct{} `type:"structure"`
	Groups      []*Group `type:"list" required:"true"`
	IsTruncated *bool    `type:"boolean"`
	Marker      *string  `min:"1" type:"string"`
}
