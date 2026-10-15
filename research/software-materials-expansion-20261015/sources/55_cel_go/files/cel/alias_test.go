// Copyright 2026 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

package cel_test

import (
	"testing"

	"github.com/google/cel-go/cel"
	canonicalcel "cel.dev/cel-go/cel"
)

func TestCelAliases(t *testing.T) {
	env, err := cel.NewEnv()
	if err != nil {
		t.Fatalf("cel.NewEnv() failed: %v", err)
	}

	var cenv *canonicalcel.Env = env
	ast, issues := cenv.Compile("1 + 2")
	if issues != nil && issues.Err() != nil {
		t.Fatalf("Compile failed: %v", issues.Err())
	}

	prg, err := env.Program(ast)
	if err != nil {
		t.Fatalf("Program failed: %v", err)
	}

	out, _, err := prg.Eval(cel.NoVars())
	if err != nil {
		t.Fatalf("Eval failed: %v", err)
	}
	if out.Value() != int64(3) {
		t.Fatalf("expected 3, got %v", out.Value())
	}
}
